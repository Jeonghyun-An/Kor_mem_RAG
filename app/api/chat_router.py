"""
채팅 API 라우터 - SSE 스트리밍
POST /api/chat  →  sources 이벤트 → token 이벤트 → done 이벤트

v2: 스토리 선정 후, 선정된 스토리는 substory(=title_sub) 전수 포함 요약(Outline Digest) 제공
"""
from __future__ import annotations

import json
import os
import re
from collections import defaultdict
from typing import Optional, List, Dict, Any, Tuple

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.services.retriever_service import retrieve_chunks
from app.services.llm_service import stream_llm
from app.services.milvus_service import get_collection

router = APIRouter(prefix="/api", tags=["chat"])

BADGES = ["포스트", "시리즈", "특집", "큐레이션", "전시", "아카이브"]

COLLECTION = os.getenv("MILVUS_COLLECTION", "korean_memory")

# ============ 컨텍스트 길이 예산(초기값) ============
TOP_STORIES = int(os.getenv("RAG_TOP_STORIES", "2"))
MAX_SUBSTORY_SNIPPET_CHARS = int(os.getenv("RAG_SUBSTORY_SNIPPET_CHARS", "600"))
MAX_CONTEXT_CHARS_TOTAL = int(os.getenv("RAG_CONTEXT_CHARS_TOTAL", "12000"))


class ChatRequest(BaseModel):
    query: str
    top_k: int = 12
    badge_filter: Optional[str] = None
    stream: bool = True


# ==================== Helpers ====================

_CHUNK_ID_RE = re.compile(r"_p(\d+)_c(\d+)$")


def _chunk_order(chunk_id: str) -> Tuple[int, int]:
    m = _CHUNK_ID_RE.search(chunk_id or "")
    if not m:
        return (10**9, 10**9)
    return (int(m.group(1)), int(m.group(2)))


def _truncate(s: str, max_chars: int) -> str:
    s = (s or "").strip()
    if len(s) <= max_chars:
        return s
    return s[: max_chars - 3].rstrip() + "..."


def _dedupe_keep_order(texts: List[str]) -> List[str]:
    seen = set()
    out = []
    for t in texts:
        key = (t or "").strip()
        if not key:
            continue
        if key in seen:
            continue
        seen.add(key)
        out.append(t)
    return out

def _pick_top_story_ids(chunks: List[Dict[str, Any]], top_n: int) -> List[str]:
    by_story: Dict[str, List[float]] = defaultdict(list)
    for c in chunks:
        item_id = c.get("item_id") or ""
        if not item_id:
            continue
        by_story[item_id].append(float(c.get("display_score", 0.0)))

    scored = []
    for item_id, scores in by_story.items():
        scores_sorted = sorted(scores, reverse=True)
        mx = scores_sorted[0]
        top2_avg = sum(scores_sorted[:2]) / min(2, len(scores_sorted))
        story_score = 0.65 * mx + 0.35 * top2_avg
        scored.append((item_id, story_score, len(scores)))

    scored.sort(key=lambda x: x[1], reverse=True)

    # 1차: 청크 2개 이상인 스토리만
    filtered = [sid for sid, _, cnt in scored if cnt >= 2][:top_n]

    # fallback: 2개 이상짜리가 없으면 그냥 상위 top_n 반환
    if not filtered:
        filtered = [sid for sid, _, _ in scored[:top_n]]

    return filtered


async def _fetch_all_chunks_for_story(item_id: str) -> List[Dict[str, Any]]:
    col = get_collection(COLLECTION, dim=1024)
    expr = f'item_id == "{item_id}"'
    rows = col.query(
        expr=expr,
        output_fields=[
            "chunk_id", "item_id", "text",
            "title_main", "title_sub", "badge",
            "keywords", "provider", "detail_url",
            "thumbnail", "date_registered", "date_modified",
            "related_stories", "related_resources",
        ],
        limit=5000,
    )

    out: List[Dict[str, Any]] = []
    for r in rows:
        kw_raw = r.get("keywords", "[]")
        if isinstance(kw_raw, str):
            try:
                keywords = json.loads(kw_raw)
            except Exception:
                keywords = []
        elif isinstance(kw_raw, list):
            keywords = kw_raw
        else:
            keywords = []

        out.append({
            "chunk_id": r.get("chunk_id", ""),
            "item_id": r.get("item_id", ""),
            "text": r.get("text", ""),
            "title_main": r.get("title_main", ""),
            "title_sub": r.get("title_sub", ""),
            "badge": r.get("badge", ""),
            "keywords": keywords,
            "provider": r.get("provider", ""),
            "detail_url": r.get("detail_url", ""),
            "thumbnail": r.get("thumbnail", ""),
            "date_registered": r.get("date_registered", ""),
        })

    out.sort(key=lambda x: _chunk_order(x.get("chunk_id", "")))
    return out


def _build_outline_context_for_story(
    query: str,
    story_chunks: List[Dict[str, Any]],
) -> Tuple[str, Dict[str, Any]]:
    if not story_chunks:
        return "", {}

    meta = story_chunks[0]
    title_main = meta.get("title_main", "")
    badge = meta.get("badge", "")
    detail_url = meta.get("detail_url", "")
    thumbnail = meta.get("thumbnail", "")
    provider = meta.get("provider", "")
    keywords = meta.get("keywords", [])

    by_sub: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for c in story_chunks:
        sub = (c.get("title_sub") or "").strip() or "서브스토리"
        by_sub[sub].append(c)

    ordered_subs = []
    seen = set()
    for c in story_chunks:
        sub = (c.get("title_sub") or "").strip() or "서브스토리"
        if sub in seen:
            continue
        seen.add(sub)
        ordered_subs.append(sub)

    sub_blocks = []
    for i, sub in enumerate(ordered_subs, start=1):
        chunks = by_sub[sub]
        texts = _dedupe_keep_order([x.get("text", "") for x in chunks])
        joined = "\n\n".join(texts)
        snippet = _truncate(joined, MAX_SUBSTORY_SNIPPET_CHARS)

        sub_blocks.append(
            f"### SUBSTORY {i}\n"
            f"- title_sub: {sub}\n"
            f"- snippet:\n{snippet}\n"
        )

    story_context = (
        f"[STORY]\n"
        f"- title_main: {title_main}\n"
        f"- badge: {badge}\n"
        f"- provider: {provider}\n"
        f"- detail_url: {detail_url}\n"
        f"- thumbnail: {thumbnail}\n"
        f"- keywords: {json.dumps(keywords, ensure_ascii=False)}\n\n"
        f"[SUBSTORIES]\n"
        + "\n".join(sub_blocks)
    )

    story_source = {
        "item_id": meta.get("item_id", ""),
        "title_main": title_main,
        "badge": badge,
        "keywords": keywords,
        "provider": provider,
        "detail_url": detail_url,
        "thumbnail": thumbnail,
        "substory_count": len(ordered_subs),
        "related_stories": meta.get("related_stories", []),
        "related_resources": meta.get("related_resources", []),
        "substories": [
            {
                "title_sub": sub,
                "detail_url": by_sub[sub][0].get("detail_url", "") if by_sub[sub] else detail_url,
                "thumbnail": by_sub[sub][0].get("thumbnail", "") if by_sub[sub] else thumbnail,
                "provider": by_sub[sub][0].get("provider", "") if by_sub[sub] else provider,
                "badge": by_sub[sub][0].get("badge", "") if by_sub[sub] else badge,
            }
            for sub in ordered_subs
        ],
    }
    return story_context, story_source


def _wrap_context_for_llm(
    query: str,
    story_contexts: List[str],
    story_sources: List[Dict[str, Any]],
) -> str:
    joined = "\n\n---\n\n".join(story_contexts)
    joined = _truncate(joined, MAX_CONTEXT_CHARS_TOTAL)

    story_titles = "\n".join(
        f"{i+1}. {s['title_main']}"
        for i, s in enumerate(story_sources)
    )

    # 헤더 예시 목록 (LLM이 정확히 따라쓰도록)
    header_examples = "\n".join(
        f"## {s['title_main']}"
        for s in story_sources
    )

    return f"""<start_of_turn>user
당신은 '코리안메모리'의 요약 전문가입니다.
제공된 [참고 자료]를 바탕으로 아래 {len(story_sources)}개의 스토리를 각각 요약하세요.

[대상 스토리 목록]
{story_titles}

[작성 가이드라인]
- 반드시 아래 헤더를 그대로 사용하여 각 블록을 시작할 것:
{header_examples}
- 각 블록은 7~10문장의 하나의 문단으로만 구성할 것.
- 모든 서브스토리의 핵심 내용을 본문에 자연스럽게 포함할 것.
- 이모지(📚, 🔗), "참고 자료", "출처", "관련 링크" 등 메타 정보를 절대 적지 마세요.
- 요약 문단이 끝나면 즉시 답변을 멈추세요.

[참고 자료]
{joined}

사용자 질문: {query}<end_of_turn>
<start_of_turn>model
"""

# ==================== SSE Generator ====================

async def _sse_generator(request: ChatRequest):
    try:
        # 1) 1차 검색
        seed_chunks = await retrieve_chunks(
            query=request.query,
            top_k=request.top_k,
            badge_filter=request.badge_filter,
        )

        # 2) 스토리 선정
        top_story_ids = _pick_top_story_ids(seed_chunks, TOP_STORIES)

        # ↓↓↓ 여기 추가 ↓↓↓
        print(f"[DEBUG] top_story_ids: {top_story_ids}")

        # 3) 선정된 스토리 전체 chunk 재조회
        story_contexts: List[str] = []
        story_sources: List[Dict[str, Any]] = []

        for sid in top_story_ids:
            all_chunks = await _fetch_all_chunks_for_story(sid)
            story_ctx, story_src = _build_outline_context_for_story(request.query, all_chunks)
            if story_ctx:
                story_contexts.append(story_ctx)
                story_sources.append(story_src)

        print(f"[DEBUG] story_sources count: {len(story_sources)}")
        for s in story_sources:
            print(f"  - {s['title_main']} / substories: {s['substory_count']}")

        # 4) sources 이벤트 전송
        yield f"event: sources\ndata: {json.dumps(story_sources, ensure_ascii=False)}\n\n"

        # 5) LLM 스트리밍 — story_sources를 함께 넘겨서 title_main 활용
        context = _wrap_context_for_llm(request.query, story_contexts, story_sources)

        # stop_markers: ## 헤더는 유지하고 불필요한 메타 섹션만 차단
        stop_markers = [ "참고 자료:", "관련 컬렉션:", "관련 자원:", "추천 키워드:", "링크:"]
        acc = ""
        sent_len = 0

        async for token in stream_llm(query=request.query, context=context):
            acc += token

            cut_positions = [acc.find(m) for m in stop_markers if acc.find(m) != -1]
            if cut_positions:
                cut_idx = min(cut_positions)
                safe_text = acc[:cut_idx]
                if len(safe_text) > sent_len:
                    remain = safe_text[sent_len:]
                    yield f"event: token\ndata: {json.dumps({'token': remain}, ensure_ascii=False)}\n\n"
                break

            if len(acc) > sent_len:
                remain = acc[sent_len:]
                sent_len = len(acc)
                yield f"event: token\ndata: {json.dumps({'token': remain}, ensure_ascii=False)}\n\n"
        print(f"[DEBUG] LLM 전체 출력:\n{acc}")
        print(f"[DEBUG] 총 출력 길이: {len(acc)} chars")
        yield f"event: done\ndata: {json.dumps({'status': 'ok'})}\n\n"

    except Exception as e:
        yield f"event: error\ndata: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"


@router.post("/chat")
async def chat(request: ChatRequest):
    return StreamingResponse(
        _sse_generator(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/badges")
async def get_badges():
    return {"badges": BADGES}
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
TOP_STORIES = int(os.getenv("RAG_TOP_STORIES", "3"))                  # 추천 스토리 개수
MAX_SUBSTORY_SNIPPET_CHARS = int(os.getenv("RAG_SUBSTORY_SNIPPET_CHARS", "1200"))  # 서브스토리별 대표 원문(추출) 길이
MAX_CONTEXT_CHARS_TOTAL = int(os.getenv("RAG_CONTEXT_CHARS_TOTAL", "22000"))       # 최종 context 총 길이


class ChatRequest(BaseModel):
    query: str
    top_k: int = 3
    badge_filter: Optional[str] = None
    stream: bool = True


# ==================== Helpers ====================

_CHUNK_ID_RE = re.compile(r"_p(\d+)_c(\d+)$")


def _chunk_order(chunk_id: str) -> Tuple[int, int]:
    """
    indexing_service.py에서 chunk_id = f"{item_id}_p{pi}_c{ci}"
    pi, ci를 파싱해서 안정적으로 정렬
    """
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
    """
    검색 결과가 섞여 들어오므로 item_id별로 스토리 점수를 만들어 상위 N개 선정
    - 점수는 display_score의 max + 상위 2개 평균을 섞어 안정화
    """
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
        scored.append((item_id, story_score))

    scored.sort(key=lambda x: x[1], reverse=True)
    return [sid for sid, _ in scored[:top_n]]


async def _fetch_all_chunks_for_story(item_id: str) -> List[Dict[str, Any]]:
    """
    선정된 스토리에 대해 Milvus에서 해당 item_id의 chunk를 전부 가져옴.
    (서브스토리 전수 포함 요구를 만족시키는 핵심)
    """
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
        limit=5000,  # 스토리당 충분히 크게
    )

    out: List[Dict[str, Any]] = []
    for r in rows:
        # keywords는 인덱싱에서 json.dumps로 들어가므로 문자열일 수 있음
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

        out.append(
            {
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
            }
        )

    out.sort(key=lambda x: _chunk_order(x.get("chunk_id", "")))
    return out


def _build_outline_context_for_story(
    query: str,
    story_chunks: List[Dict[str, Any]],
) -> Tuple[str, Dict[str, Any]]:
    """
    서브스토리(title_sub) 전수 포함 ‘목차형 다이제스트’를 만들기 위한 컨텍스트 생성.
    - LLM에는 "서브스토리별 대표 snippet"만 주고
    - 출력은 "서브스토리 전부 1~2문장 요약"을 강제
    """
    if not story_chunks:
        return "", {}

    meta = story_chunks[0]
    title_main = meta.get("title_main", "")
    badge = meta.get("badge", "")
    detail_url = meta.get("detail_url", "")
    thumbnail = meta.get("thumbnail", "")
    provider = meta.get("provider", "")
    keywords = meta.get("keywords", [])

    # title_sub별로 묶기
    by_sub: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for c in story_chunks:
        sub = (c.get("title_sub") or "").strip() or "서브스토리"
        by_sub[sub].append(c)

    # 서브스토리 순서 유지(등장 순)
    ordered_subs = []
    seen = set()
    for c in story_chunks:
        sub = (c.get("title_sub") or "").strip() or "서브스토리"
        if sub in seen:
            continue
        seen.add(sub)
        ordered_subs.append(sub)

    # 서브스토리별 대표 snippet 만들기 (원문 전부 X, 길이 제한 O)
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
        "related_stories": meta.get("related_stories", []),    # 추가
        "related_resources": meta.get("related_resources", []), # 추가
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

def _build_ui_sources(chunks: List[Dict[str, Any]], limit: int = 12) -> List[Dict[str, Any]]:
    """
    프론트 relatedResources / relatedCollections / relatedKeywords 용 카드 데이터
    """
    out: List[Dict[str, Any]] = []
    seen = set()

    for c in chunks:
        key = c.get("chunk_id") or f"{c.get('item_id','')}_{c.get('title_sub','')}"
        if not key or key in seen:
            continue
        seen.add(key)

        out.append(
            {
                "chunk_id": c.get("chunk_id", ""),
                "item_id": c.get("item_id", ""),
                "title_main": c.get("title_main", ""),
                "title_sub": c.get("title_sub", ""),
                "badge": c.get("badge", ""),
                "keywords": c.get("keywords", []) or [],
                "provider": c.get("provider", ""),
                "detail_url": c.get("detail_url", ""),
                "thumbnail": c.get("thumbnail", ""),
                "score": round(float(c.get("display_score", 0.0)), 3),
                "text_preview": (c.get("text", "") or "")[:200],
            }
        )

        if len(out) >= limit:
            break

    return out
def _wrap_context_for_llm(query: str, story_contexts: List[str]) -> str:
    joined = "\n\n---\n\n".join(story_contexts)
    joined = _truncate(joined, MAX_CONTEXT_CHARS_TOTAL)

    return f"""
당신은 코리안메모리 AI 어시스턴트입니다.
사용자 질문에 대해 제공된 자료만 바탕으로 자연스럽고 간결한 '질의 요약'만 작성하세요.

절대 규칙:
1. 답변은 본문 요약만 작성합니다.
2. "참고 자료", "관련 컬렉션", "관련 자원", "링크", "추천 키워드" 같은 제목이나 섹션을 절대 출력하지 마세요.
3. 목록형(-, 1), 2))으로 쓰지 말고 자연스러운 문단형 설명으로 작성하세요.
4. 4~7문장 정도의 한국어 문단으로 작성하세요.
5. 자료에 없는 내용은 추측하지 마세요.
6. 본문 마지막에 링크나 제목 목록을 붙이지 마세요.
7. 출력은 오직 요약 본문만 생성하세요.

사용자 질문:
{query}

참고 자료:
{joined}
""".strip()

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

        # 3) 선정된 스토리 전체 chunk 재조회
        story_contexts: List[str] = []
        story_sources: List[Dict[str, Any]] = []          # ← 추가

        for sid in top_story_ids:
            all_chunks = await _fetch_all_chunks_for_story(sid)
            story_ctx, story_src = _build_outline_context_for_story(request.query, all_chunks)  # ← _ 제거
            if story_ctx:
                story_contexts.append(story_ctx)
                story_sources.append(story_src)           # ← 수집

        # 4) sources 이벤트: substories 포함된 story_sources 전송  ← 핵심 변경
        yield f"event: sources\ndata: {json.dumps(story_sources, ensure_ascii=False)}\n\n"

        # 5) 통합 요약 생성
        context = _wrap_context_for_llm(request.query, story_contexts)

        stop_markers = ["📚", "참고 자료", "관련 컬렉션", "관련 자원", "추천 키워드", "링크:"]
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
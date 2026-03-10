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
    top_k: int = 8
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
            "thumbnail", "date_registered",
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
    }
    return story_context, story_source


def _wrap_context_for_llm(query: str, story_contexts: List[str]) -> str:
    """
    llm_service.stream_llm(query, context)에 들어갈 최종 context.
    SYSTEM_PROMPT는 그대로 두고, 여기서 출력 형식/규칙을 강제한다.
    """
    # 너무 길면 전체 context를 잘라서 안전장치
    joined = "\n\n---\n\n".join(story_contexts)
    joined = _truncate(joined, MAX_CONTEXT_CHARS_TOTAL)

    return f"""
[작업 지시]
당신은 아래 [STORY]들의 [SUBSTORIES]를 기반으로 답해야 합니다.

필수 규칙:
1) 각 STORY마다 "서브스토리(title_sub)"를 빠짐없이 전부 포함해서 요약하세요.
2) 각 서브스토리는 최대 2문장으로 요약하세요.
3) 맨 위에 STORY별로 3~5줄 '전체 요약'을 먼저 제공합니다.
4) 사용자의 질문("{query}")과 직접 관련된 포인트를 우선 배치하고, 관련이 낮은 서브스토리는 더 짧게 써도 됩니다(하지만 누락 금지).
5) 자료에 없는 내용은 추측하지 말고 "제공된 자료에서 찾을 수 없습니다"라고 명시하세요.
6) 각 STORY 블록 끝에는 '추천 키워드'와 '링크'를 반드시 포함하세요.

[출력 포맷(고정)]
## 추천 스토리 1: <title_main>
- 한줄 요약: ...
- 전체 요약:
  - ...
  - ...
- 서브스토리 목차 요약:
  1) <title_sub>: (최대 2문장)
  2) <title_sub>: (최대 2문장)
  ...
- 추천 키워드: ...
- 링크: ...

(스토리 2, 3도 동일)

[참고 자료]
{joined}
""".strip()


# ==================== SSE Generator ====================

async def _sse_generator(request: ChatRequest):
    try:
        # 1) 1차 검색 (스토리 후보 확보)
        seed_chunks = await retrieve_chunks(
            query=request.query,
            top_k=request.top_k,
            badge_filter=request.badge_filter,
        )

        # 2) 스토리 2~3개 선정
        top_story_ids = _pick_top_story_ids(seed_chunks, TOP_STORIES)

        # 3) 선정된 스토리의 "전체 chunk"를 Milvus에서 재조회 (전수 포함)
        story_contexts: List[str] = []
        story_sources: List[Dict[str, Any]] = []

        for sid in top_story_ids:
            all_chunks = await _fetch_all_chunks_for_story(sid)
            story_ctx, story_src = _build_outline_context_for_story(request.query, all_chunks)
            if story_ctx:
                story_contexts.append(story_ctx)
                story_sources.append(story_src)

        # 4) sources 이벤트 (UI용: 선정된 스토리 단위로 내려줌)
        yield f"event: sources\ndata: {json.dumps(story_sources, ensure_ascii=False)}\n\n"

        # 5) LLM context 구성 (서브스토리 전수 포함 요약 강제)
        context = _wrap_context_for_llm(request.query, story_contexts)

        async for token in stream_llm(query=request.query, context=context):
            yield f"event: token\ndata: {json.dumps({'token': token}, ensure_ascii=False)}\n\n"

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
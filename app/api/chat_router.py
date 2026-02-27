"""
채팅 API 라우터 - SSE 스트리밍
POST /api/chat  →  sources 이벤트 → token 이벤트 → done 이벤트
"""
from __future__ import annotations
import json
import os
from typing import Optional, List
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.services.retriever_service import retrieve_chunks
from app.services.llm_service import stream_llm

router = APIRouter(prefix="/api", tags=["chat"])

BADGES = ["포스트", "시리즈", "특집", "큐레이션", "전시", "아카이브"]


class ChatRequest(BaseModel):
    query: str
    top_k: int = 8
    badge_filter: Optional[str] = None
    stream: bool = True


async def _sse_generator(request: ChatRequest):
    """SSE 이벤트 스트림 생성기"""
    try:
        # 1. 관련 청크 검색
        chunks = await retrieve_chunks(
            query=request.query,
            top_k=request.top_k,
            badge_filter=request.badge_filter,
        )

        # 2. sources 이벤트 전송
        sources_payload = [
            {
                "chunk_id": c.get("chunk_id", ""),
                "title_main": c.get("title_main", ""),
                "title_sub": c.get("title_sub", ""),
                "badge": c.get("badge", ""),
                "keywords": c.get("keywords", []),
                "provider": c.get("provider", ""),
                "detail_url": c.get("detail_url", ""),
                "thumbnail": c.get("thumbnail", ""),
                "score": round(c.get("display_score", 0.0), 3),
                "text_preview": c.get("text", "")[:120],
            }
            for c in chunks
        ]
        yield f"event: sources\ndata: {json.dumps(sources_payload, ensure_ascii=False)}\n\n"

        # 3. LLM 스트리밍 토큰
        context = "\n\n---\n\n".join(
            f"[출처: {c.get('title_main', '')} / {c.get('badge', '')}]\n{c.get('text', '')}"
            for c in chunks
        )

        async for token in stream_llm(query=request.query, context=context):
            yield f"event: token\ndata: {json.dumps({'token': token}, ensure_ascii=False)}\n\n"

        # 4. done 이벤트
        yield f"event: done\ndata: {json.dumps({'status': 'ok'})}\n\n"

    except Exception as e:
        yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"


@router.post("/chat")
async def chat(request: ChatRequest):
    return StreamingResponse(
        _sse_generator(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Nginx 버퍼링 비활성화
        },
    )


@router.get("/badges")
async def get_badges():
    return {"badges": BADGES}

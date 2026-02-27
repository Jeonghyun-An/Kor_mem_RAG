"""
검색 API 라우터 (LLM 없이 벡터 검색만)
GET /api/search?q=...&top_k=8&badge=포스트
"""
from __future__ import annotations
from typing import Optional
from fastapi import APIRouter, Query
from app.services.retriever_service import retrieve_chunks

router = APIRouter(prefix="/api", tags=["search"])


@router.get("/search")
async def search(
    q: str = Query(..., description="검색 쿼리"),
    top_k: int = Query(8, ge=1, le=20),
    badge: Optional[str] = Query(None, description="배지 필터"),
):
    chunks = await retrieve_chunks(query=q, top_k=top_k, badge_filter=badge)
    return {
        "query": q,
        "total": len(chunks),
        "results": [
            {
                "chunk_id": c.get("chunk_id"),
                "title_main": c.get("title_main"),
                "title_sub": c.get("title_sub"),
                "badge": c.get("badge"),
                "keywords": c.get("keywords", []),
                "provider": c.get("provider"),
                "detail_url": c.get("detail_url"),
                "thumbnail": c.get("thumbnail"),
                "score": round(c.get("display_score", 0.0), 3),
                "text_preview": c.get("text", "")[:200],
            }
            for c in chunks
        ],
    }

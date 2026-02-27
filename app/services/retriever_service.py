"""
검색 서비스 - BGE-M3 임베딩 → Milvus HNSW(IP) 검색 → Min-Max 정규화
"""
from __future__ import annotations
import os
import json
from typing import Optional, List, Dict, Any

from app.services.embedding_service import encode
from app.services.milvus_service import get_collection

COLLECTION = os.getenv("MILVUS_COLLECTION", "korean_memory")
SCORE_THRESHOLD = float(os.getenv("RAG_SCORE_THRESHOLD", "0.1"))


def _normalize_minmax(scores: list[float]) -> list[float]:
    if not scores:
        return []
    lo, hi = min(scores), max(scores)
    if hi - lo < 1e-9:
        return [1.0] * len(scores)
    return [(s - lo) / (hi - lo) for s in scores]


async def retrieve_chunks(
    query: str,
    top_k: int = 8,
    badge_filter: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    쿼리 → 임베딩 → Milvus 검색 → 점수 정규화 → 반환
    """
    # 1. 쿼리 임베딩
    q_emb = encode([query], normalize=True)[0]

    # 2. Milvus 검색
    col = get_collection(COLLECTION, dim=1024)

    expr = f'badge == "{badge_filter}"' if badge_filter else None

    results = col.search(
        data=[q_emb],
        anns_field="embedding",
        param={"metric_type": "IP", "params": {"ef": 256}},
        limit=top_k * 2,
        expr=expr,
        output_fields=[
            "chunk_id", "item_id", "text",
            "title_main", "title_sub", "badge",
            "keywords", "provider", "detail_url",
            "thumbnail", "date_registered",
        ],
    )

    # 3. 파싱
    hits = []
    for hit in results[0]:
        ent = hit.entity
        hits.append({
            "chunk_id":       ent.get("chunk_id", ""),
            "item_id":        ent.get("item_id", ""),
            "text":           ent.get("text", ""),
            "title_main":     ent.get("title_main", ""),
            "title_sub":      ent.get("title_sub", ""),
            "badge":          ent.get("badge", ""),
            "keywords":       json.loads(ent.get("keywords", "[]")),
            "provider":       ent.get("provider", ""),
            "detail_url":     ent.get("detail_url", ""),
            "thumbnail":      ent.get("thumbnail", ""),
            "date_registered": ent.get("date_registered", ""),
            "raw_score":      float(hit.score),
        })

    # 4. Min-Max 정규화
    raw_scores = [h["raw_score"] for h in hits]
    norm = _normalize_minmax(raw_scores)
    for i, h in enumerate(hits):
        h["display_score"] = norm[i]

    # 5. 임계값 필터 + top_k 자르기
    filtered = [h for h in hits if h["display_score"] >= SCORE_THRESHOLD]
    return filtered[:top_k]

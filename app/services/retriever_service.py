# app/services/retriever_service.py

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


def _safe_entity_get(ent, key: str, default=None):
    try:
        value = ent.get(key)
        return default if value is None else value
    except Exception:
        return default


async def retrieve_chunks(
    query: str,
    top_k: int = 8,
    badge_filter: Optional[str] = None,
) -> List[Dict[str, Any]]:
    q_emb = encode([query], normalize=True)[0]

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

    hits: List[Dict[str, Any]] = []

    for hit in results[0]:
        ent = hit.entity

        kw_raw = _safe_entity_get(ent, "keywords", "[]")
        if isinstance(kw_raw, str):
            try:
                keywords = json.loads(kw_raw)
            except Exception:
                keywords = []
        elif isinstance(kw_raw, list):
            keywords = kw_raw
        else:
            keywords = []

        hits.append({
            "chunk_id": _safe_entity_get(ent, "chunk_id", ""),
            "item_id": _safe_entity_get(ent, "item_id", ""),
            "text": _safe_entity_get(ent, "text", ""),
            "title_main": _safe_entity_get(ent, "title_main", ""),
            "title_sub": _safe_entity_get(ent, "title_sub", ""),
            "badge": _safe_entity_get(ent, "badge", ""),
            "keywords": keywords,
            "provider": _safe_entity_get(ent, "provider", ""),
            "detail_url": _safe_entity_get(ent, "detail_url", ""),
            "thumbnail": _safe_entity_get(ent, "thumbnail", ""),
            "date_registered": _safe_entity_get(ent, "date_registered", ""),
            "raw_score": float(hit.score),
        })

    raw_scores = [h["raw_score"] for h in hits]
    norm = _normalize_minmax(raw_scores)

    for i, h in enumerate(hits):
        h["display_score"] = norm[i]

    filtered = [h for h in hits if h["display_score"] >= SCORE_THRESHOLD]
    return filtered[:top_k]
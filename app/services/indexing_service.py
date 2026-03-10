"""
인덱싱 서비스 - collected_data.json → 청킹 → BGE-M3 임베딩 → Milvus HNSW
"""
from __future__ import annotations

import json
import os
import re
import uuid
from pathlib import Path
from typing import List, Dict, Any

from app.services.embedding_service import encode, BATCH_SIZE
from app.services.milvus_service import get_collection, drop_collection

DATA_PATH = Path(os.getenv("DATA_PATH", "/app/data/collected_data.json"))
COLLECTION = os.getenv("MILVUS_COLLECTION", "korean_memory")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "600"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "100"))

# VARCHAR 길이 제한 (milvus_service.py와 맞춰야 함)
MAX_LEN_CHUNK_ID = 128
MAX_LEN_ITEM_ID = 64
MAX_LEN_TITLE_MAIN = 512
MAX_LEN_TITLE_SUB = 512
MAX_LEN_BADGE = 64
MAX_LEN_KEYWORDS = 2048
MAX_LEN_PROVIDER = 512
MAX_LEN_DETAIL_URL = 1024
MAX_LEN_THUMBNAIL = 1024
MAX_LEN_DATE = 64
MAX_LEN_RELATED_STORIES = 4096
MAX_LEN_RELATED_RESOURCES = 4096


# ==================== 유틸 ====================

def _fit_varchar(value: str, max_len: int) -> str:
    value = value or ""
    if len(value) <= max_len:
        return value
    return value[:max_len]


def _normalize_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        v = value.strip()
        if not v:
            return []
        try:
            parsed = json.loads(v)
            if isinstance(parsed, list):
                return parsed
        except Exception:
            return [v]
    return []


def _normalize_keywords(value) -> list[str]:
    arr = _normalize_list(value)
    out = []
    for x in arr:
        s = str(x).strip()
        if s:
            out.append(s)
    return out


def _dedupe_keep_order(values: List[str]) -> List[str]:
    seen = set()
    out = []
    for v in values:
        vv = (v or "").strip()
        if not vv or vv in seen:
            continue
        seen.add(vv)
        out.append(vv)
    return out


def _compact_related_stories(items: list) -> list:
    compact = []
    for x in (items or [])[:10]:
        if isinstance(x, dict):
            compact.append({
                "title": str(x.get("title", ""))[:200],
                "url": str(x.get("url", ""))[:500],
            })
        else:
            compact.append(str(x)[:300])
    return compact


def _compact_related_resources(items: list) -> list:
    compact = []
    for x in (items or [])[:10]:
        if isinstance(x, dict):
            compact.append({
                "title": str(x.get("title", ""))[:200],
                "url": str(x.get("url", ""))[:500],
                "type": str(x.get("type", ""))[:100],
            })
        else:
            compact.append(str(x)[:300])
    return compact


# ==================== 청킹 ====================

def _split_text(
    text: str,
    size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> List[str]:
    """단락 경계 우선, max size 기반 청킹"""
    paragraphs = re.split(r"\n{2,}", text.strip())
    chunks, buf = [], ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        if len(buf) + len(para) + 2 <= size:
            buf = (buf + "\n\n" + para).strip()
        else:
            if buf:
                chunks.append(buf)
                overlap_text = buf[-overlap:] if len(buf) > overlap else buf
                buf = (overlap_text + "\n\n" + para).strip()
            else:
                step = max(1, size - overlap)
                for i in range(0, len(para), step):
                    chunks.append(para[i:i + size])
                buf = ""

    if buf:
        chunks.append(buf)

    return chunks


def _make_chunks(item: Dict[str, Any]) -> List[Dict[str, Any]]:
    item_id = str(item.get("data_idx", uuid.uuid4()))
    title_main = item.get("title_main") or item.get("title", "")
    badge = item.get("badge", "")
    thumbnail = item.get("thumbnail", "")

    sub_pages = item.get("sub_pages", [])
    chunks: List[Dict[str, Any]] = []

    for pi, page in enumerate(sub_pages):
        title_sub = page.get("title_sub", "")
        detail_url = page.get("detail_url", "")
        detail = page.get("detail", {}) or {}

        provider = detail.get("provider", "")
        date_registered = detail.get("date_registered", "")
        date_modified = detail.get("date_modified", "")
        body_text = detail.get("body_text", "") or ""

        detail_keywords = _normalize_keywords(detail.get("keywords"))
        related_stories = _compact_related_stories(_normalize_list(detail.get("related_stories")))
        related_resources = _compact_related_resources(_normalize_list(detail.get("related_resources")))

        # keywords fallback
        keywords = detail_keywords
        if not keywords:
            fallback = []
            if title_main:
                fallback.append(str(title_main).strip())
            if title_sub:
                fallback.append(str(title_sub).strip())
            keywords = fallback

        keywords = _dedupe_keep_order(keywords)[:20]

        if not body_text.strip():
            continue

        keywords_json = _fit_varchar(
            json.dumps(keywords, ensure_ascii=False),
            MAX_LEN_KEYWORDS,
        )
        related_stories_json = _fit_varchar(
            json.dumps(related_stories, ensure_ascii=False),
            MAX_LEN_RELATED_STORIES,
        )
        related_resources_json = _fit_varchar(
            json.dumps(related_resources, ensure_ascii=False),
            MAX_LEN_RELATED_RESOURCES,
        )

        for ci, text in enumerate(_split_text(body_text)):
            chunk_id = f"{item_id}_p{pi}_c{ci}"

            chunks.append({
                "chunk_id": _fit_varchar(chunk_id, MAX_LEN_CHUNK_ID),
                "item_id": _fit_varchar(item_id, MAX_LEN_ITEM_ID),
                "text": text,
                "title_main": _fit_varchar(str(title_main), MAX_LEN_TITLE_MAIN),
                "title_sub": _fit_varchar(str(title_sub), MAX_LEN_TITLE_SUB),
                "badge": _fit_varchar(str(badge), MAX_LEN_BADGE),
                "keywords": keywords_json,
                "provider": _fit_varchar(str(provider), MAX_LEN_PROVIDER),
                "detail_url": _fit_varchar(str(detail_url), MAX_LEN_DETAIL_URL),
                "thumbnail": _fit_varchar(str(thumbnail), MAX_LEN_THUMBNAIL),
                "date_registered": _fit_varchar(str(date_registered), MAX_LEN_DATE),
                "date_modified": _fit_varchar(str(date_modified), MAX_LEN_DATE),
                "related_stories": related_stories_json,
                "related_resources": related_resources_json,
            })

    return chunks


# ==================== 메인 인덱싱 ====================

async def run_full_index():
    """collected_data.json 전체 인덱싱"""
    print("[INDEX] Starting full indexing...")

    if not DATA_PATH.exists():
        print(f"[INDEX] ✗ Data file not found: {DATA_PATH}")
        return

    with open(DATA_PATH, encoding="utf-8") as f:
        raw = json.load(f)

    items: List[Dict[str, Any]] = (
        raw if isinstance(raw, list)
        else raw.get("items", list(raw.values()))
    )
    print(f"[INDEX] Loaded {len(items)} items")

    all_chunks: List[Dict[str, Any]] = []
    for item in items:
        all_chunks.extend(_make_chunks(item))

    print(f"[INDEX] Total chunks: {len(all_chunks)}")

    if not all_chunks:
        print("[INDEX] No chunks generated")
        return

    drop_collection(COLLECTION)
    col = get_collection(COLLECTION, dim=1024)

    batch_size = BATCH_SIZE
    for start in range(0, len(all_chunks), batch_size):
        batch = all_chunks[start:start + batch_size]
        texts = [c["text"] for c in batch]
        embeddings = encode(texts, normalize=True)

        embeddings = [list(map(float, vec)) for vec in embeddings]

        if len(embeddings) != len(batch):
            raise RuntimeError(
                f"[INDEX] embedding row mismatch: batch={len(batch)}, embeddings={len(embeddings)}"
            )

        if embeddings and len(embeddings[0]) != 1024:
            raise RuntimeError(
                f"[INDEX] embedding dim mismatch: expected 1024, got {len(embeddings[0])}"
            )

        entities = [
            [c["chunk_id"] for c in batch],
            [c["item_id"] for c in batch],
            [c["text"] for c in batch],
            [c["title_main"] for c in batch],
            [c["title_sub"] for c in batch],
            [c["badge"] for c in batch],
            [c["keywords"] for c in batch],
            [c["provider"] for c in batch],
            [c["detail_url"] for c in batch],
            [c["thumbnail"] for c in batch],
            [c["date_registered"] for c in batch],
            embeddings,
            [c["date_modified"] for c in batch],
            [c["related_stories"] for c in batch],
            [c["related_resources"] for c in batch],
        ]

        col.insert(entities)
        print(f"[INDEX]   Inserted {start + len(batch)}/{len(all_chunks)}")

    col.flush()
    print(f"[INDEX] ✓ Done. Total: {col.num_entities} chunks in Milvus")
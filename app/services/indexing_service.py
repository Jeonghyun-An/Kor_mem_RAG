"""
인덱싱 서비스 - collected_data.json → 청킹 → BGE-M3 임베딩 → Milvus HNSW
"""
from __future__ import annotations
import json
import os
import re
import uuid
from pathlib import Path
from typing import List, Dict, Any, Tuple

from app.services.embedding_service import encode, BATCH_SIZE
from app.services.milvus_service import get_collection, drop_collection

DATA_PATH   = Path(os.getenv("DATA_PATH", "/app/data/collected_data.json"))
COLLECTION  = os.getenv("MILVUS_COLLECTION", "korean_memory")
CHUNK_SIZE  = int(os.getenv("CHUNK_SIZE", "600"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "100"))


# ==================== 청킹 ====================

def _split_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
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
                # overlap
                overlap_text = buf[-overlap:] if len(buf) > overlap else buf
                buf = (overlap_text + "\n\n" + para).strip()
            else:
                # 단락 자체가 너무 긴 경우 강제 분할
                for i in range(0, len(para), size - overlap):
                    chunks.append(para[i:i + size])
                buf = ""
    if buf:
        chunks.append(buf)
    return chunks


def _make_chunks(item: Dict) -> List[Dict]:
    """하나의 item → 복수 chunk dict"""
    item_id = str(item.get("id", uuid.uuid4()))
    title_main = item.get("title", "")
    badge = item.get("badge", "")
    keywords = item.get("keywords", [])
    provider = item.get("provider", "")
    date_registered = str(item.get("date_registered", ""))
    date_modified   = str(item.get("date_modified", ""))
    detail_url      = item.get("detail_url", "")
    thumbnail       = item.get("thumbnail", "")

    # sub_pages에서 본문 수집
    sub_pages = item.get("sub_pages", [])
    chunks = []
    for pi, page in enumerate(sub_pages):
        title_sub = page.get("title", "")
        content   = page.get("content", "")
        if not content:
            continue
        for ci, text in enumerate(_split_text(content)):
            chunk_id = f"{item_id}_p{pi}_c{ci}"
            chunks.append({
                "chunk_id":       chunk_id,
                "item_id":        item_id,
                "text":           text,
                "title_main":     title_main,
                "title_sub":      title_sub,
                "badge":          badge,
                "keywords":       json.dumps(keywords, ensure_ascii=False),
                "provider":       provider,
                "detail_url":     detail_url,
                "thumbnail":      thumbnail,
                "date_registered": date_registered,
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

    # 리스트 또는 딕셔너리 둘 다 처리
    items: List[Dict] = raw if isinstance(raw, list) else list(raw.values())
    print(f"[INDEX] Loaded {len(items)} items")

    # 청킹
    all_chunks: List[Dict] = []
    for item in items:
        all_chunks.extend(_make_chunks(item))
    print(f"[INDEX] Total chunks: {len(all_chunks)}")

    if not all_chunks:
        print("[INDEX] No chunks generated")
        return

    # 컬렉션 초기화
    drop_collection(COLLECTION)
    col = get_collection(COLLECTION, dim=1024)

    # 배치 임베딩 & 삽입
    batch_size = BATCH_SIZE
    for start in range(0, len(all_chunks), batch_size):
        batch = all_chunks[start:start + batch_size]
        texts = [c["text"] for c in batch]
        embeddings = encode(texts, normalize=True)

        entities = [
            [c["chunk_id"]       for c in batch],
            [c["item_id"]        for c in batch],
            [c["text"]           for c in batch],
            [c["title_main"]     for c in batch],
            [c["title_sub"]      for c in batch],
            [c["badge"]          for c in batch],
            [c["keywords"]       for c in batch],
            [c["provider"]       for c in batch],
            [c["detail_url"]     for c in batch],
            [c["thumbnail"]      for c in batch],
            [c["date_registered"] for c in batch],
            embeddings,
        ]
        col.insert(entities)
        print(f"[INDEX]   Inserted {start + len(batch)}/{len(all_chunks)}")

    col.flush()
    print(f"[INDEX] ✓ Done. Total: {col.num_entities} chunks in Milvus")

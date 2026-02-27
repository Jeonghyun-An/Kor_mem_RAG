"""
Milvus 서비스 - HNSW / IP metric (Library_AI_land와 동일)
포트: 19531 (내부 컨테이너 간은 19530)
컬렉션: korean_memory
"""
from __future__ import annotations
import os
import time
from typing import Optional
from pymilvus import (
    connections, Collection, CollectionSchema,
    FieldSchema, DataType, utility
)

_COLLECTION_CACHE: dict = {}

MILVUS_HOST = os.getenv("MILVUS_HOST", "localhost")
MILVUS_PORT = os.getenv("MILVUS_PORT", "19530")


def ensure_connected(retries: int = 10, backoff: float = 2.0):
    try:
        connections.connect("default", host=MILVUS_HOST, port=MILVUS_PORT, timeout=10)
        print(f"[MILVUS] Connected to {MILVUS_HOST}:{MILVUS_PORT}")
    except Exception as e:
        for i in range(retries):
            print(f"[MILVUS] Retry {i+1}/{retries} ...")
            time.sleep(backoff)
            try:
                connections.connect("default", host=MILVUS_HOST, port=MILVUS_PORT, timeout=10)
                return
            except Exception:
                pass
        raise RuntimeError(f"Milvus 연결 실패: {e}")


def get_collection(name: str, dim: int = 1024) -> Collection:
    if name in _COLLECTION_CACHE:
        return _COLLECTION_CACHE[name]

    ensure_connected()

    if not utility.has_collection(name):
        _create_collection(name, dim)

    col = Collection(name)
    col.load()
    _COLLECTION_CACHE[name] = col
    return col


def _create_collection(name: str, dim: int):
    """Korean Memory 컬렉션 스키마 생성"""
    fields = [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
        FieldSchema(name="chunk_id",     dtype=DataType.VARCHAR, max_length=128),
        FieldSchema(name="item_id",      dtype=DataType.VARCHAR, max_length=64),
        FieldSchema(name="text",         dtype=DataType.VARCHAR, max_length=4096),
        FieldSchema(name="title_main",   dtype=DataType.VARCHAR, max_length=512),
        FieldSchema(name="title_sub",    dtype=DataType.VARCHAR, max_length=512),
        FieldSchema(name="badge",        dtype=DataType.VARCHAR, max_length=32),
        FieldSchema(name="keywords",     dtype=DataType.VARCHAR, max_length=512),
        FieldSchema(name="provider",     dtype=DataType.VARCHAR, max_length=256),
        FieldSchema(name="detail_url",   dtype=DataType.VARCHAR, max_length=1024),
        FieldSchema(name="thumbnail",    dtype=DataType.VARCHAR, max_length=1024),
        FieldSchema(name="date_registered", dtype=DataType.VARCHAR, max_length=32),
        FieldSchema(name="embedding",    dtype=DataType.FLOAT_VECTOR, dim=dim),
    ]
    schema = CollectionSchema(fields, description="Korean Memory RAG chunks")
    col = Collection(name, schema)

    # HNSW 인덱스 (Library_AI_land와 동일)
    col.create_index(
        field_name="embedding",
        index_params={
            "metric_type": "IP",
            "index_type": "HNSW",
            "params": {"M": 16, "efConstruction": 200},
        },
    )
    print(f"[MILVUS] Collection '{name}' created with HNSW/IP index")
    return col


def drop_collection(name: str):
    ensure_connected()
    if utility.has_collection(name):
        utility.drop_collection(name)
        _COLLECTION_CACHE.pop(name, None)
        print(f"[MILVUS] Collection '{name}' dropped")

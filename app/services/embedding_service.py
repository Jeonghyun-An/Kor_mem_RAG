"""
BGE-M3 임베딩 싱글톤 (Library_AI_land와 동일 모델/방식)
"""
from __future__ import annotations
import os
from typing import Optional
from sentence_transformers import SentenceTransformer

_model: Optional[SentenceTransformer] = None
MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "BAAI/bge-m3")
BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", "32"))
MAX_LENGTH = int(os.getenv("EMBEDDING_MAX_LENGTH", "512"))


def get_embedding_model() -> SentenceTransformer:
    global _model
    if _model is None:
        print(f"[EMBED] Loading {MODEL_NAME} ...")
        _model = SentenceTransformer(MODEL_NAME, cache_folder="/models")
        _model.max_seq_length = MAX_LENGTH
        print(f"[EMBED] {MODEL_NAME} loaded (dim=1024)")
    return _model


def encode(texts: list[str], normalize: bool = True) -> list[list[float]]:
    model = get_embedding_model()
    embeddings = model.encode(
        texts,
        batch_size=BATCH_SIZE,
        normalize_embeddings=normalize,
        show_progress_bar=False,
    )
    return embeddings.tolist()

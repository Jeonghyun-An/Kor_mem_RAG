"""
코리안메모리 RAG 시스템 - FastAPI 메인
내부 포트: 8000  |  외부 노출: 18001:8000  (Library_AI_land: 18000:8000)
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os, time

from app.api.chat_router import router as chat_router
from app.api.search_router import router as search_router
from app.api.index_router import router as index_router

app = FastAPI(
    title="Korean Memory RAG API",
    description="코리안메모리 지식검색 RAG 시스템",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(search_router)
app.include_router(index_router)


@app.get("/")
async def root():
    return {"service": "Korean Memory RAG API", "version": "1.0.0", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.on_event("startup")
async def startup():
    start = time.time()
    print("=" * 60)
    print("Korean Memory RAG System Starting...")
    print("=" * 60)

    # Milvus 연결
    print("\n[1/3] Milvus 연결 확인...")
    try:
        from app.services.milvus_service import ensure_connected
        ensure_connected()
        print("  ✓ Milvus OK")
    except Exception as e:
        print(f"  ✗ Milvus not ready (will retry on demand): {e}")

    # MinIO 버킷
    print("\n[2/3] MinIO 초기화...")
    try:
        from app.services.minio_service import get_minio_client
        client = get_minio_client()
        bucket = os.getenv("MINIO_BUCKET", "kormem-bucket")
        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)
            print(f"  ✓ Bucket '{bucket}' created")
        else:
            print(f"  ✓ Bucket '{bucket}' exists")
    except Exception as e:
        print(f"  ✗ MinIO error: {e}")

    # Embedding 모델 워밍업
    print("\n[3/3] Embedding 모델 로드...")
    try:
        from app.services.embedding_service import get_embedding_model
        get_embedding_model()
        print("  ✓ BGE-M3 loaded")
    except Exception as e:
        print(f"  ✗ Embedding error: {e}")

    print(f"\n✅ Startup complete in {time.time() - start:.1f}s")

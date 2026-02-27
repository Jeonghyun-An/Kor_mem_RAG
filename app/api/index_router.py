"""
인덱싱 API - collected_data.json → Milvus
POST /api/index/run   : 전체 인덱싱 실행
GET  /api/index/stats : 컬렉션 통계
DELETE /api/index/reset : 컬렉션 초기화
"""
from __future__ import annotations
import os
from fastapi import APIRouter, BackgroundTasks, HTTPException
from app.services.milvus_service import get_collection, drop_collection

router = APIRouter(prefix="/api/index", tags=["index"])


@router.post("/run")
async def run_indexing(background_tasks: BackgroundTasks):
    """백그라운드로 인덱싱 실행"""
    from app.services.indexing_service import run_full_index
    background_tasks.add_task(run_full_index)
    return {"status": "started", "message": "인덱싱이 백그라운드에서 시작되었습니다."}


@router.get("/stats")
async def get_stats():
    """Milvus 컬렉션 통계"""
    try:
        collection_name = os.getenv("MILVUS_COLLECTION", "korean_memory")
        col = get_collection(collection_name, dim=1024)
        col.load()
        count = col.num_entities
        return {"collection": collection_name, "total_chunks": count, "status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/reset")
async def reset_index():
    """컬렉션 전체 삭제 후 재생성"""
    try:
        collection_name = os.getenv("MILVUS_COLLECTION", "korean_memory")
        drop_collection(collection_name)
        return {"status": "reset", "message": f"컬렉션 '{collection_name}' 초기화 완료"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

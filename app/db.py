from __future__ import annotations

import os
from datetime import datetime
from typing import Optional, Dict, Any, List

from motor.motor_asyncio import (
    AsyncIOMotorClient,
    AsyncIOMotorDatabase,
    AsyncIOMotorCollection,
    AsyncIOMotorGridFSBucket,
)
from pymongo import ASCENDING, DESCENDING
from bson import ObjectId

from app.models import RunningJobDoc, JobType

# === 환경 변수 ===
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "leadgen_db")

# === 전역 핸들 ===
_client: Optional[AsyncIOMotorClient] = None
_db: Optional[AsyncIOMotorDatabase] = None
col_jobs: Optional[AsyncIOMotorCollection] = None
col_running: Optional[AsyncIOMotorCollection] = None
gridfs_bucket: Optional[AsyncIOMotorGridFSBucket] = None


# === 초기화/종료 ===

async def init_db(app=None) -> None:
    """
    앱 시작 시 호출: Mongo 연결 및 인덱스 준비
    """
    global _client, _db, col_jobs, col_running, gridfs_bucket
    _client = AsyncIOMotorClient(MONGO_URI)
    _db = _client[MONGO_DB_NAME]
    col_jobs = _db["jobs"]
    col_running = _db["running_jobs"]
    gridfs_bucket = AsyncIOMotorGridFSBucket(_db)

    # 인덱스(필수만)
    await col_jobs.create_index([("job_id", ASCENDING)], unique=True)
    await col_jobs.create_index([("sub", ASCENDING), ("created_at", DESCENDING)])
    await col_running.create_index([("sub", ASCENDING)], unique=True)

    if app:
        @app.on_event("shutdown")
        async def _close():
            await close_db()

async def close_db() -> None:
    global _client
    if _client:
        _client.close()
        _client = None


# === running_jobs: 유저당 진행중 매핑 ===

async def upsert_running_job(sub: str, job_id: str) -> None:
    """
    유저당 진행중 job 매핑(sub→job_id) 저장/갱신. (유저당 1개 가정)
    """
    assert col_running is not None
    doc = RunningJobDoc(sub=sub, job_id=job_id).model_dump()
    await col_running.update_one({"sub": sub}, {"$set": doc}, upsert=True)

async def get_running_job_by_sub(sub: str) -> Optional[str]:
    """
    진행중 job_id 반환 (없으면 None)
    """
    assert col_running is not None
    doc = await col_running.find_one({"sub": sub})
    return doc["job_id"] if doc else None

async def clear_running_job(sub: str) -> None:
    """
    진행 완료/실패/취소 시 매핑 제거
    """
    assert col_running is not None
    await col_running.delete_one({"sub": sub})


# === jobs: 최종 메타만 기록/조회 ===
# (진행률/중간 상태는 메모리 task_status에서만 관리)

async def record_job_started(job_id: str, sub: str, job_type: JobType) -> None:
    """
    (선택) 시작 시점 기록. 굳이 안 써도 됨. 쓰면 이력에 'running' 흔적 남김.
    """
    assert col_jobs is not None
    now = datetime.utcnow()
    doc = {
        "job_id": job_id,
        "sub": sub,
        "type": job_type,
        "status": "running",
        "created_at": now,
    }
    await col_jobs.update_one({"job_id": job_id}, {"$setOnInsert": doc}, upsert=True)

async def record_job_completed(
    job_id: str,
    sub: str,
    *,
    job_type: JobType,
    result_filename: str,
    file_id: str,
    size: int,
    content_type: str = "text/csv",
) -> None:
    """
    완료 시 최종 메타 기록.
    """
    assert col_jobs is not None
    await col_jobs.update_one(
        {"job_id": job_id},
        {
            "$set": {
                "job_id": job_id,
                "sub": sub,
                "type": job_type,
                "result_filename": result_filename,
                "file_id": file_id,
                "size": size,
                "content_type": content_type,
                "finished_at": datetime.utcnow(),
            },
            "$setOnInsert": {
                "created_at": datetime.utcnow(),
            },
        },
        upsert=True,
    )

async def record_job_failed(job_id: str, sub: str, status: str, error_msg: str | None) -> None:
    """
    실패/취소 등 최종 상태 기록. status ∈ {"failed","cancelled"}
    """
    assert col_jobs is not None
    await col_jobs.update_one(
        {"job_id": job_id},
        {
            "$set": {
                "sub": sub,
                "status": status,  # "failed" | "cancelled"
                "error": error_msg,
                "finished_at": datetime.utcnow(),
            },
            "$setOnInsert": {
                "created_at": datetime.utcnow(),
            },
        },
        upsert=True,
    )

async def list_completed_files(sub: str, *, limit: int = 100) -> List[Dict[str, Any]]:
    """
    해당 유저가 완료한 파일들 최신순 리스트
    """
    assert col_jobs is not None
    cur = col_jobs.find(
        {"sub": sub},
        sort=[("created_at", DESCENDING)],
        projection={"job_id": 1, "result_filename": 1, "created_at": 1, "size": 1},
        limit=limit,
    )
    return [doc async for doc in cur]

async def is_file_owned_by(sub: str, filename: str) -> bool:
    """
    파일 다운로드 권한 확인용: 이 파일이 해당 유저의 완료 결과인지 검사
    """
    assert col_jobs is not None
    doc = await col_jobs.find_one({"sub": sub, "result_filename": filename})
    return bool(doc)

async def get_file_doc_by_filename(sub: str, filename: str) -> Optional[Dict[str, Any]]:
    """
    파일 메타 조회: 해당 유저의 파일 문서. file_id, size 포함
    """
    assert col_jobs is not None
    return await col_jobs.find_one(
        {"sub": sub, "result_filename": filename},
        projection={"_id": 0, "job_id": 1, "result_filename": 1, "file_id": 1, "size": 1, "content_type": 1},
    )

async def get_latest_job_meta(sub: str) -> Optional[Dict[str, Any]]:
    """
    최근 작업 메타(상태/파일명 등 최종 메타) 1건. 진행중이 없을 때 상태 요약 용도로 사용 가능.
    """
    assert col_jobs is not None
    return await col_jobs.find_one({"sub": sub}, sort=[("created_at", DESCENDING)])

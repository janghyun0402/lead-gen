# from fastapi import FastAPI
# from pydantic import BaseModel
# import time
# import logging
# from typing import Dict
# from fastapi import BackgroundTasks, HTTPException, File, UploadFile
# import uuid
# import os
# from fastapi.responses import FileResponse
# from fastapi.middleware.cors import CORSMiddleware

# from run import csv_mode, city_mode, multi_city_mode

# # --- 로깅 설정 ---
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)


# app = FastAPI()

# # 프런트 도메인/포트만 넣으세요
# ORIGINS = [
#     "http://localhost:7860",
#     "http://127.0.0.1:7860",
#     "http://172.178.117.69:7860",
#     "https://pm-collector.kindredpm.ai:7860",
#     "https://pm-collector.kindredpm.ai",  # 배포 시 80 포트로 접근하는 경우
# ]

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=ORIGINS,       # 필요 시 ["*"] 가능(보안 약함)
#     allow_credentials=True,      # 쿠키/세션 필요 없으면 False
#     allow_methods=["*"],         # 혹은 ["GET","POST","PUT","PATCH","DELETE","OPTIONS"]
#     allow_headers=["*"],         # "Authorization","Content-Type" 등 커스텀 헤더 허용
# )

# # 작업 상태를 저장할 글로벌 변수 (In-memory DB 역할)
# # 실제 프로덕션에서는 Redis나 DB를 사용하는 것이 좋습니다.
# task_status: Dict[str, Dict] = {}


# class CityAnalysisRequest(BaseModel):
#     city: str

# class CSVAnalysisRequest(BaseModel):
#     file: UploadFile = File(...)




# class AnalysisRequest(BaseModel):
#     city: str
        
        
# # --- 백그라운드 작업 함수 ---
# def run_city_analysis(job_id: str, city_name: str):
#     """도시 이름 기반 분석을 백그라운드에서 실행"""
#     logger.info(f"✅ [Job ID: {job_id}] City analysis for '{city_name}' started.")
#     task_status[job_id] = {"status": "running", "start_time": time.time()}
    
#     try:
#         # 비동기 함수를 동기적으로 실행해야 할 경우 asyncio.run 사용
#         import asyncio
#         result_path = asyncio.run(city_mode(city_name, max_results_per_city=1, max_pages=15, max_depth=3, use_browser=True))
        
#         task_status[job_id].update({"status": "completed", "result_path": result_path})
#         logger.info(f"🎉 [Job ID: {job_id}] City analysis for '{city_name}' finished.")
#     except Exception as e:
#         task_status[job_id].update({"status": "failed", "error": str(e)})
#         logger.error(f"❌ [Job ID: {job_id}] City analysis for '{city_name}' failed: {e}")

# def run_csv_analysis(job_id: str, file_content: bytes, original_filename: str):
#     """CSV 파일 기반 분석을 백그라운드에서 실행"""
#     logger.info(f"✅ [Job ID: {job_id}] CSV analysis for '{original_filename}' started.")
#     task_status[job_id] = {"status": "running", "start_time": time.time()}

#     # 백그라운드 작업에서 파일을 처리하기 위해 임시 파일로 저장
#     temp_file_path = f"temp_{job_id}_{original_filename}"
#     with open(temp_file_path, "wb") as f:
#         f.write(file_content)

#     try:
#         import asyncio
#         result_path = asyncio.run(csv_mode(temp_file_path))

#         task_status[job_id].update({"status": "completed", "result_path": result_path})
#         logger.info(f"🎉 [Job ID: {job_id}] CSV analysis for '{original_filename}' finished.")
#     except Exception as e:
#         task_status[job_id].update({"status": "failed", "error": str(e)})
#         logger.error(f"❌ [Job ID: {job_id}] CSV analysis for '{original_filename}' failed: {e}")



# # --- API 엔드포인트 ---
# @app.post("/city")
# async def start_city_analysis(request: CityAnalysisRequest, background_tasks: BackgroundTasks):
#     job_id = str(uuid.uuid4())
#     background_tasks.add_task(run_city_analysis, job_id, request.city)
#     return {"message": "City analysis started.", "job_id": job_id}

# @app.post("/csv")
# async def start_csv_analysis(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
#     job_id = str(uuid.uuid4())
#     file_content = await file.read() # 파일 내용을 미리 읽어둠
#     background_tasks.add_task(run_csv_analysis, job_id, file_content, file.filename)
#     return {"message": "CSV analysis started.", "job_id": job_id}


# @app.get("/status/{job_id}")
# async def get_analysis_status(job_id: str):
#     status = task_status.get(job_id)
#     if not status:
#         raise HTTPException(status_code=404, detail="Job ID not found.")
#     return status

# # ▼▼▼ 파일 다운로드 엔드포인트 추가 ▼▼▼
# RESULTS_DIR = "outputs"
# @app.get("/download/{filename}")
# async def download_file(filename: str):
#     file_path = os.path.join(RESULTS_DIR, filename)
#     if os.path.exists(file_path):
#         return FileResponse(path=file_path, media_type='text/csv', filename=filename)
#     raise HTTPException(status_code=404, detail="File not found.")

from fastapi import FastAPI
from pydantic import BaseModel
import time
import logging
from typing import Dict
from fastapi import HTTPException, File, UploadFile, Depends, Header
import uuid
import os
from fastapi.responses import FileResponse, Response
from fastapi.middleware.cors import CORSMiddleware
import asyncio  # asyncio 임포트
from typing import Optional
from starlette.responses import StreamingResponse
from bson import ObjectId
from io import BytesIO

from google.oauth2 import id_token
from google.auth.transport import requests as grequests

from run import csv_mode, city_mode, multi_city_mode
import app.db as db
from app.db import (
    init_db,
    upsert_running_job,
    get_running_job_by_sub,
    clear_running_job,
    record_job_completed,
    list_completed_files,
    get_file_doc_by_filename,
)

# --- 로깅 설정 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


app = FastAPI()

# 프런트 도메인/포트만 넣으세요
ORIGINS = [
    "http://localhost:7860",
    "http://127.0.0.1:7860",
    "http://localhost:5173",  # Vite 기본 포트
    "http://127.0.0.1:5173",  # Vite 기본 포트
    "http://172.178.117.69:7860",
    "https://pm-collector.kindredpm.ai:7860",
    "https://pm-collector.kindredpm.ai",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 작업 상태와 asyncio.Task 객체를 함께 저장합니다.
task_status: Dict[str, Dict] = {}


class CityAnalysisRequest(BaseModel):
    city: str
    max_results_per_city: int = 2


# --- 앱 시작 시 DB 초기화 ---
@app.on_event("startup")
async def _startup():
    await init_db(app)


# --- 인증 헬퍼 ---
ALLOWED_EMAIL_DOMAIN = os.getenv("ALLOWED_EMAIL_DOMAIN", "kindredpm.ai")

async def get_current_user(Authorization: str = Header(None)) -> Dict[str, str]:
    if not Authorization or not Authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token")
    token = Authorization.split(" ", 1)[1].strip()
    try:
        claims = id_token.verify_oauth2_token(token, grequests.Request(), audience=None)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    issuer = claims.get("iss")
    if issuer not in {"accounts.google.com", "https://accounts.google.com"}:
        raise HTTPException(status_code=401, detail="Invalid issuer")

    email = claims.get("email", "")
    if not email.endswith(ALLOWED_EMAIL_DOMAIN):
        raise HTTPException(status_code=403, detail="Unauthorized domain")

    sub = claims.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    return {"sub": sub, "email": email}


# --- 비동기 백그라운드 작업 함수 ---
async def run_city_analysis(job_id: str, sub: str, city_name: str, max_results_per_city: int = 2):
    """도시 이름 기반 분석을 백그라운드에서 실행 (비동기 및 취소 가능, 다중 도시 지원)"""
    logger.info(f"✅ [Job ID: {job_id}] City analysis for '{city_name}' started.")
    
    task_status[job_id].update({
        "status": "running", 
        "start_time": time.time(),
        "progress": {
            "current": int(0),
            "total": int(0)
        }
        })
    
    # run.py의 city_mode, multi_city_mode에서 호출되는 callback 함수
    # NOTE: to_thread로 실행 시 스레드 안전하게 진행률 반영을 위해 loop.call_soon_threadsafe 사용
    loop = asyncio.get_running_loop()
    def _inc():
        task_status[job_id]["progress"]["current"] += 1
        logger.info(f"📊 [Job ID: {job_id}] Progress: {task_status[job_id]['progress']['current']}/{task_status[job_id]['progress']['total']}")
    def progress_callback_increment():
        try:
            loop.call_soon_threadsafe(_inc)
        except RuntimeError:
            _inc()
    def _set_total(v: int):
        task_status[job_id]["progress"]["total"] = v
    def progress_callback_init_total(total: int):
        try:
            loop.call_soon_threadsafe(lambda: _set_total(total))
        except RuntimeError:
            _set_total(total)
        

    
    try:
        # Check if city_name contains comma (multiple cities)
        if ',' in city_name:
            logger.info(f"🌆 [Job ID: {job_id}] Detected multiple cities: {city_name}")
            result_filename = await multi_city_mode(
                city_name, max_results_per_city=max_results_per_city, max_pages=15, max_depth=3, 
                use_browser=True, progress_callback_increment=progress_callback_increment, progress_callback_init_total=progress_callback_init_total)
        else:
            logger.info(f"🏙️  [Job ID: {job_id}] Processing single city: {city_name}")
            # NOTE: heavy pipeline -> run only city_mode in a separate thread via to_thread
            result_filename = await asyncio.to_thread(
                lambda: asyncio.run(
                    city_mode(
                        city_name, max_results_per_city=max_results_per_city, max_pages=15, max_depth=3,
                        use_browser=True, progress_callback_increment=progress_callback_increment, progress_callback_init_total=progress_callback_init_total
                    )
                )
            )
        
        task_status[job_id].update({"status": "completed", "result_filename": result_filename})
        # 업로드 to GridFS
        file_path = os.path.join("outputs", result_filename)
        try:
            with open(file_path, "rb") as f:
                data = f.read()
        except FileNotFoundError:
            # city/multi returns filename only; ensure path exists
            raise
        assert db.gridfs_bucket is not None
        file_id = await db.gridfs_bucket.upload_from_stream(result_filename, BytesIO(data))
        logger.info(f"[GridFS] uploaded city CSV: {result_filename} ({len(data)} bytes) -> {file_id}")
        await record_job_completed(
            job_id,
            sub,
            job_type="city",
            result_filename=result_filename,
            file_id=str(file_id),
            size=len(data),
            content_type="text/csv",
        )
        try:
            os.remove(file_path)
        except Exception:
            pass
        logger.info(f"🎉 [Job ID: {job_id}] City analysis for '{city_name}' finished.")
    except asyncio.CancelledError:
        # 취소 요청이 들어오면 이 예외가 발생합니다.
        task_status[job_id].update({"status": "cancelled", "error": "Cancelled by user"})
        logger.info(f"🛑 [Job ID: {job_id}] Task was successfully cancelled by user request.")
    except Exception as e:
        task_status[job_id].update({"status": "failed", "error": str(e)})
        logger.error(f"❌ [Job ID: {job_id}] City analysis for '{city_name}' failed: {e}")

async def run_csv_analysis(job_id: str, sub: str, file_content: bytes, original_filename: str):
    """CSV 파일 기반 분석을 백그라운드에서 실행 (비동기 및 취소 가능)"""
    logger.info(f"✅ [Job ID: {job_id}] CSV analysis for '{original_filename}' started.")
    task_status[job_id].update({
        "status": "running", 
        "start_time": time.time(),
        "progress": {
            "current": int(0),
            "total": int(0)
        }
        })

    # NOTE: to_thread로 실행 시 스레드 안전하게 진행률 반영을 위해 loop.call_soon_threadsafe 사용
    loop = asyncio.get_running_loop()
    def _inc():
        task_status[job_id]["progress"]["current"] += 1
        logger.info(f"📊 [Job ID: {job_id}] Progress: {task_status[job_id]['progress']['current']}/{task_status[job_id]['progress']['total']}")
    def progress_callback_increment():
        try:
            loop.call_soon_threadsafe(_inc)
        except RuntimeError:
            _inc()
    def _set_total(v: int):
        task_status[job_id]["progress"]["total"] = v
    def progress_callback_init_total(total: int):
        try:
            loop.call_soon_threadsafe(lambda: _set_total(total))
        except RuntimeError:
            _set_total(total)

    temp_file_path = f"temp_{job_id}_{original_filename}"
    with open(temp_file_path, "wb") as f:
        f.write(file_content)

    try:
        # NOTE: heavy pipeline -> run only csv_mode in a separate thread via to_thread
        result_path = await asyncio.to_thread(
            lambda: asyncio.run(
                csv_mode(
                    temp_file_path, max_pages=15, max_depth=3, use_browser=True, progress_callback_increment=progress_callback_increment, progress_callback_init_total=progress_callback_init_total
                )
            )
        )

        result_filename = os.path.basename(result_path) if result_path else None
        task_status[job_id].update({"status": "completed", "result_filename": result_filename})
        # 업로드 to GridFS
        assert db.gridfs_bucket is not None
        file_path = result_path if result_path and os.path.exists(result_path) else os.path.join("outputs", result_filename or "")
        with open(file_path, "rb") as f:
            data = f.read()
        up_name = result_filename or original_filename
        
        assert db.gridfs_bucket is not None
        file_id = await db.gridfs_bucket.upload_from_stream(up_name, BytesIO(data))
        logger.info(f"[GridFS] uploaded csv CSV: {up_name} ({len(data)} bytes) -> {file_id}")
        await record_job_completed(
            job_id,
            sub,
            job_type="csv",
            result_filename=up_name,
            file_id=str(file_id),
            size=len(data),
            content_type="text/csv",
        )
        try:
            os.remove(file_path)
        except Exception:
            pass
        logger.info(f"🎉 [Job ID: {job_id}] CSV analysis for '{original_filename}' finished.")
    except asyncio.CancelledError:
        task_status[job_id].update({"status": "cancelled", "error": "Cancelled by user"})
        logger.info(f"🛑 [Job ID: {job_id}] Task was successfully cancelled by user request.")
    except Exception as e:
        task_status[job_id].update({"status": "failed", "error": str(e)})
        logger.error(f"❌ [Job ID: {job_id}] CSV analysis for '{original_filename}' failed: {e}")
    finally:
        
        # input .csv file 삭제
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)


# --- API 엔드포인트 ---
@app.post("/city")
async def start_city_analysis(request: CityAnalysisRequest, user: Dict[str, str] = Depends(get_current_user)):
    sub = user["sub"]
    existing = await get_running_job_by_sub(sub)
    if existing:
        raise HTTPException(status_code=409, detail="Job already running")
    job_id = str(uuid.uuid4())
    task_status[job_id] = {"status": "running"}
    # DB에는 완료된 결과만 저장하기로 하여 시작 기록은 남기지 않음
    await upsert_running_job(sub, job_id)
    task = asyncio.create_task(run_city_analysis(job_id, sub, request.city, request.max_results_per_city))
    task_status[job_id]["task"] = task
    return {"message": "City analysis started.", "job_id": job_id}

@app.post("/csv")
async def start_csv_analysis(file: UploadFile = File(...), user: Dict[str, str] = Depends(get_current_user)):
    sub = user["sub"]
    existing = await get_running_job_by_sub(sub)
    if existing:
        raise HTTPException(status_code=409, detail="Job already running")
    job_id = str(uuid.uuid4())
    task_status[job_id] = {"status": "running"}
    # DB에는 완료된 결과만 저장하기로 하여 시작 기록은 남기지 않음
    await upsert_running_job(sub, job_id)
    file_content = await file.read() 
    task = asyncio.create_task(run_csv_analysis(job_id, sub, file_content, file.filename))
    task_status[job_id]["task"] = task
    return {"message": "CSV analysis started.", "job_id": job_id}


class JobStatusResponse(BaseModel):
    status: str
    error: Optional[str] = None
    result_filename: Optional[str] = None
    start_time: Optional[float] = None
    current: Optional[int] = None
    total: Optional[int] = None


@app.get("/status")
async def get_my_status(user: Dict[str, str] = Depends(get_current_user)):
    sub = user["sub"]
    job_id = await get_running_job_by_sub(sub)
    if not job_id:
        raise HTTPException(status_code=404, detail="No running job")
    status = task_status.get(job_id)
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")
    status_to_return = status.copy()
    status_to_return.pop("task", None)
    status_to_return["current"] = status_to_return.get("progress", {}).get("current")
    status_to_return["total"] = status_to_return.get("progress", {}).get("total")
    # terminal 상태면 running 매핑 제거
    if status_to_return.get("status") in {"completed", "failed", "cancelled"}:
        await clear_running_job(sub)
    return status_to_return

# ▼▼▼ 수정된 작업 취소 엔드포인트 ▼▼▼
@app.post("/cancel")
async def cancel_my_analysis(user: Dict[str, str] = Depends(get_current_user)):
    """현재 유저의 진행중 작업을 취소"""
    sub = user["sub"]
    job_id = await get_running_job_by_sub(sub)
    if not job_id:
        raise HTTPException(status_code=404, detail="No running job")
    job_info = task_status.get(job_id)
    if not job_info:
        raise HTTPException(status_code=404, detail="Job not found")
    if job_info.get("status") in ["completed", "failed", "cancelled"]:
        return {"message": "Job is already in a final state."}
    task = job_info.get("task")
    if task and not task.done():
        task.cancel()
        logger.info(f"👉 [Job ID: {job_id}] Cancellation request sent to the task.")
        return {"message": "Analysis cancellation requested.", "job_id": job_id}
    else:
        job_info.update({"status": "cancelled", "error": "Cancelled by user"})
        logger.warning(f"👉 [Job ID: {job_id}] Task not found or already done. Marked as cancelled.")
        return {"message": "Analysis marked as cancelled.", "job_id": job_id}


# ▼▼▼ 파일 다운로드 엔드포인트 (변경 없음) ▼▼▼
RESULTS_DIR = "outputs"
@app.get("/files")
async def get_my_files(user: Dict[str, str] = Depends(get_current_user)):
    sub = user["sub"]
    files = await list_completed_files(sub)
    def _fmt(doc: Dict) -> Dict:
        return {
            "job_id": doc.get("job_id"),
            "result_filename": doc.get("result_filename"),
            "created_at": doc.get("created_at"),
            "size": doc.get("size"),
            "download_url": f"/download/{doc.get('result_filename')}",
        }
    return {"files": [_fmt(d) for d in files]}

@app.get("/download/{filename}")
async def download_file(filename: str, user: Dict[str, str] = Depends(get_current_user)):
    sub = user["sub"]
    doc = await get_file_doc_by_filename(sub, filename)
    if not doc:
        raise HTTPException(status_code=404, detail="File not found")
    
    if db.gridfs_bucket is None:
        raise HTTPException(status_code=500, detail="GridFS bucket not found")
    file_id = doc.get("file_id")
    if not file_id:
        raise HTTPException(status_code=404, detail="File not found")
    
    grid_out = await db.gridfs_bucket.open_download_stream(ObjectId(file_id))
    data = await grid_out.read()
    media_type = doc.get("content_type") or "text/csv"
    headers = {"Content-Disposition": f"attachment; filename={filename}"}
    return Response(content=data, media_type=media_type, headers=headers)


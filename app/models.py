from __future__ import annotations
from typing import Literal
from datetime import datetime
from pydantic import BaseModel, Field

JobType = Literal["city", "csv"]

class CompletedJobDoc(BaseModel):
    job_id: str
    sub: str                     # Google user ID (sub)
    type: JobType
    result_filename: str         # 원본 파일명
    file_id: str                 # GridFS ObjectId(hex string)
    size: int                    # 바이트 사이즈
    content_type: str = "text/csv"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    finished_at: datetime = Field(default_factory=datetime.utcnow)
    
class RunningJobDoc(BaseModel):
    sub: str
    job_id: str
    updated_at: datetime = Field(default_factory=datetime.utcnow)

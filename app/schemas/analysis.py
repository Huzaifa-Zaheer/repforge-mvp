from pydantic import BaseModel
from typing import List
from uuid import UUID

class AnalysisRequest(BaseModel):
    set_ids: List[UUID]

class AnalysisResponse(BaseModel):
    job_id: str
    status: str

class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    result: dict = None

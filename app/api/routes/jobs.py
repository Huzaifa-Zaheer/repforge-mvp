from fastapi import APIRouter, HTTPException
from app.schemas.analysis import JobStatusResponse
from app.services.jobs import JobService

router = APIRouter()

@router.get("/{job_id}", response_model=JobStatusResponse)
def get_job_status(job_id: str):
    job = JobService.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

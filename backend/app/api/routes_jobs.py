from fastapi import APIRouter

from app.api.dto.jobs import JobResponse

router = APIRouter()


@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: str) -> JobResponse:
    return JobResponse(id=job_id, project_id="project_demo", status="queued")


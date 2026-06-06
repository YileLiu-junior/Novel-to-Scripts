from fastapi import APIRouter, HTTPException

from app.api.dto.jobs import JobResponse
from app.domain.jobs import GenerationJob
from app.services.job_service import JobService

router = APIRouter()


def _job_response(job: GenerationJob) -> JobResponse:
    return JobResponse(
        id=job.id,
        project_id=job.project_id,
        status=job.status,
        current_step=job.current_step,
        error=job.error,
        artifact_ids=job.artifact_ids,
    )


@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: str) -> JobResponse:
    job = JobService().get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")
    return _job_response(job)

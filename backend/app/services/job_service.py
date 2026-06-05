from __future__ import annotations

from app.domain.jobs import GenerationJob, JobStatus


class JobService:
    def create_job(self, project_id: str) -> GenerationJob:
        return GenerationJob(id=f"job_{project_id}_001", project_id=project_id)

    def mark_step(self, job: GenerationJob, status: JobStatus, step: str | None = None, error: str | None = None) -> GenerationJob:
        return job.model_copy(update={"status": status, "current_step": step, "error": error})


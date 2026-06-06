from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.domain.jobs import GenerationJob, JobStatus
from app.repositories.job_repository import JobRepository


class JobService:
    def __init__(self, repository: JobRepository | None = None) -> None:
        self.repository = repository or JobRepository()

    def create_job(self, project_id: str) -> GenerationJob:
        timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
        job = GenerationJob(id=f"job_{timestamp}_{uuid4().hex[:8]}", project_id=project_id)
        return self.repository.save(job)

    def mark_step(self, job: GenerationJob, status: JobStatus, step: str | None = None, error: str | None = None) -> GenerationJob:
        persisted = self.repository.get(job.id)
        artifact_ids = persisted.artifact_ids if persisted is not None else job.artifact_ids
        updated = job.model_copy(
            update={"status": status, "current_step": step, "error": error, "artifact_ids": artifact_ids}
        )
        return self.repository.save(updated)

    def get_job(self, job_id: str) -> GenerationJob | None:
        return self.repository.get(job_id)

    def append_artifact(self, job_id: str, artifact_id: str) -> GenerationJob | None:
        job = self.repository.get(job_id)
        if job is None:
            return None
        artifact_ids = [*job.artifact_ids]
        if artifact_id not in artifact_ids:
            artifact_ids.append(artifact_id)
        return self.repository.save(job.model_copy(update={"artifact_ids": artifact_ids}))

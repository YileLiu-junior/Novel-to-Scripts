from __future__ import annotations

from app.domain.jobs import GenerationJob


class JobRepository:
    def save(self, job: GenerationJob) -> GenerationJob:
        return job

    def get(self, job_id: str) -> GenerationJob | None:
        return None


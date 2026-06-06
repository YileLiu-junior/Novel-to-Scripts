from __future__ import annotations

from pathlib import Path

from app.domain.jobs import GenerationJob
from app.repositories.file_store import default_data_root, read_json, write_json_atomic


class JobRepository:
    def __init__(self, data_root: Path | None = None) -> None:
        self.data_root = data_root or default_data_root()

    def _path_for_project(self, project_id: str) -> Path:
        return self.data_root / "projects" / project_id / "jobs.json"

    def save(self, job: GenerationJob) -> GenerationJob:
        path = self._path_for_project(job.project_id)
        records = read_json(path, {})
        records[job.id] = job.model_dump(mode="json")
        write_json_atomic(path, records)
        return job

    def get(self, job_id: str) -> GenerationJob | None:
        projects_root = self.data_root / "projects"
        if not projects_root.exists():
            return None
        for jobs_path in projects_root.glob("*/jobs.json"):
            records = read_json(jobs_path, {})
            data = records.get(job_id)
            if data is not None:
                return GenerationJob.model_validate(data)
        return None

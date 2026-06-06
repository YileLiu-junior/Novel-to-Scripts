from __future__ import annotations

from typing import Any

from app.domain.artifacts import Artifact, ArtifactType
from app.repositories.artifact_repository import ArtifactRepository
from app.services.job_service import JobService


class ArtifactService:
    def __init__(
        self,
        repository: ArtifactRepository | None = None,
        job_service: JobService | None = None,
    ) -> None:
        self.repository = repository or ArtifactRepository()
        self.job_service = job_service or JobService()

    def save_artifact(
        self,
        project_id: str,
        artifact_type: ArtifactType,
        data: dict[str, Any] | str,
        job_id: str | None = None,
    ) -> Artifact:
        version = self.repository.next_version(project_id, artifact_type)
        artifact = Artifact(
            id=f"artifact_{project_id}_{artifact_type}_v{version:03d}",
            project_id=project_id,
            job_id=job_id,
            type=artifact_type,
            version=version,
            data=data,
        )
        saved = self.repository.save(artifact)
        if job_id is not None:
            self.job_service.append_artifact(job_id, saved.id)
        return saved

    def list_for_project(self, project_id: str) -> list[Artifact]:
        return self.repository.list_for_project(project_id)

    def latest_for_project(self, project_id: str, artifact_type: str) -> Artifact | None:
        return self.repository.latest_for_project(project_id, artifact_type)

    def get_for_project(self, project_id: str, artifact_id_or_type: str) -> Artifact | None:
        return self.repository.get(project_id, artifact_id_or_type)

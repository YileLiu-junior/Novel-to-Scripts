from __future__ import annotations

from app.domain.artifacts import Artifact


class ArtifactRepository:
    def save(self, artifact: Artifact) -> Artifact:
        return artifact

    def list_for_project(self, project_id: str) -> list[Artifact]:
        return []


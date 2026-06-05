from __future__ import annotations

from typing import Any

from app.domain.artifacts import Artifact, ArtifactType


class ArtifactService:
    def save_artifact(
        self,
        project_id: str,
        artifact_type: ArtifactType,
        data: dict[str, Any] | str,
        job_id: str | None = None,
    ) -> Artifact:
        return Artifact(
            id=f"artifact_{project_id}_{artifact_type}_v1",
            project_id=project_id,
            job_id=job_id,
            type=artifact_type,
            version=1,
            data=data,
        )


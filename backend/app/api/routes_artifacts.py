from fastapi import APIRouter, HTTPException

from app.api.dto.artifacts import ArtifactResponse
from app.domain.artifacts import Artifact
from app.services.artifact_service import ArtifactService
from app.services.project_service import ProjectService

router = APIRouter()


def _artifact_response(artifact: Artifact) -> ArtifactResponse:
    return ArtifactResponse(
        id=artifact.id,
        type=artifact.type,
        version=artifact.version,
        data=artifact.data,
    )


@router.get("/{project_id}/artifacts", response_model=list[ArtifactResponse])
def list_artifacts(project_id: str) -> list[ArtifactResponse]:
    if ProjectService().get_project(project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    return [_artifact_response(artifact) for artifact in ArtifactService().list_for_project(project_id)]


@router.get("/{project_id}/artifacts/{artifact_type}", response_model=ArtifactResponse)
def get_artifact(project_id: str, artifact_type: str) -> ArtifactResponse:
    if ProjectService().get_project(project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    artifact = ArtifactService().get_for_project(project_id, artifact_type)
    if artifact is None:
        raise HTTPException(status_code=404, detail="Artifact not found.")
    return _artifact_response(artifact)

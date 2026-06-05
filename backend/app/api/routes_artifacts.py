from fastapi import APIRouter

from app.api.dto.artifacts import ArtifactResponse

router = APIRouter()


@router.get("/{project_id}/artifacts", response_model=list[ArtifactResponse])
def list_artifacts(project_id: str) -> list[ArtifactResponse]:
    return []


@router.get("/{project_id}/artifacts/{artifact_type}", response_model=ArtifactResponse)
def get_artifact(project_id: str, artifact_type: str) -> ArtifactResponse:
    return ArtifactResponse(id=f"artifact_{project_id}_{artifact_type}_v1", type=artifact_type, version=1, data={})


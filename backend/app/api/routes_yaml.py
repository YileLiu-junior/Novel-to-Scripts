from fastapi import APIRouter, HTTPException, Response

from app.api.dto.yaml import ValidateYamlRequest, ValidateYamlResponse
from app.services.project_service import ProjectService
from app.services.yaml_service import YamlService

router = APIRouter()


@router.post("/{project_id}/yaml/validate", response_model=ValidateYamlResponse)
def validate_yaml(project_id: str, request: ValidateYamlRequest) -> ValidateYamlResponse:
    findings = YamlService().validate_yaml(request.yaml_text)
    return ValidateYamlResponse(findings=[finding.model_dump() for finding in findings])


@router.get("/{project_id}/yaml/download")
def download_yaml(project_id: str) -> Response:
    if ProjectService().get_project(project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    yaml_text = YamlService().download_latest_for_project(project_id)
    if yaml_text is None:
        raise HTTPException(status_code=404, detail="No screenplay_yaml artifact exists for this project yet.")
    return Response(
        content=yaml_text,
        media_type="application/x-yaml",
        headers={"Content-Disposition": 'attachment; filename="screenplay.yaml"'},
    )

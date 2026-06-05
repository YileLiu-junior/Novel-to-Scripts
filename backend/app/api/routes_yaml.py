from fastapi import APIRouter, HTTPException

from app.api.dto.yaml import ValidateYamlRequest, ValidateYamlResponse
from app.services.yaml_service import YamlService

router = APIRouter()


@router.post("/{project_id}/yaml/validate", response_model=ValidateYamlResponse)
def validate_yaml(project_id: str, request: ValidateYamlRequest) -> ValidateYamlResponse:
    findings = YamlService().validate_yaml(request.yaml_text)
    return ValidateYamlResponse(findings=[finding.model_dump() for finding in findings])


@router.get("/{project_id}/yaml/download")
def download_yaml(project_id: str) -> str:
    raise HTTPException(status_code=404, detail="No screenplay_yaml artifact exists for this project yet.")


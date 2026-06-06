from pydantic import BaseModel


class ValidateYamlRequest(BaseModel):
    yaml_text: str


class ValidationFindingResponse(BaseModel):
    code: str
    severity: str
    message: str
    target_type: str | None = None
    target_id: str | None = None
    path: str | None = None
    schema_path: str | None = None


class ValidateYamlResponse(BaseModel):
    findings: list[ValidationFindingResponse]

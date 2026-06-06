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
<<<<<<< HEAD
=======
    schema_path: str | None = None
>>>>>>> 7be98a4 (feat: add screenplay schema design and JSON/YAML definitions)


class ValidateYamlResponse(BaseModel):
    findings: list[ValidationFindingResponse]
<<<<<<< HEAD

=======
>>>>>>> 7be98a4 (feat: add screenplay schema design and JSON/YAML definitions)

from pydantic import BaseModel


class JobResponse(BaseModel):
    id: str
    project_id: str
    status: str
    current_step: str | None = None
    error: str | None = None
    artifact_ids: list[str] = []


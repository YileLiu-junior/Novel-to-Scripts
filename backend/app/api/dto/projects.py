from pydantic import BaseModel


class CreateProjectRequest(BaseModel):
    title: str
    logline: str | None = None
    target_format: str = "web_series"


class ProjectResponse(BaseModel):
    id: str
    title: str
    logline: str | None = None
    target_format: str


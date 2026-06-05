from fastapi import APIRouter

from app.api.dto.projects import CreateProjectRequest, ProjectResponse

router = APIRouter()


@router.post("", response_model=ProjectResponse)
def create_project(request: CreateProjectRequest) -> ProjectResponse:
    return ProjectResponse(
        id="project_demo",
        title=request.title,
        logline=request.logline,
        target_format=request.target_format,
    )


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: str) -> ProjectResponse:
    return ProjectResponse(id=project_id, title="Demo Project", target_format="web_series")


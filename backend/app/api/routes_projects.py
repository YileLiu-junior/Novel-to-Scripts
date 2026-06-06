from fastapi import APIRouter, HTTPException

from app.api.dto.projects import CreateProjectRequest, ProjectResponse
from app.domain.project import Project
from app.services.project_service import ProjectService

router = APIRouter()


def _project_response(project: Project) -> ProjectResponse:
    return ProjectResponse(
        id=project.id,
        title=project.title,
        logline=project.logline,
        target_format=project.target_format,
    )


@router.post("", response_model=ProjectResponse)
def create_project(request: CreateProjectRequest) -> ProjectResponse:
    project = ProjectService().create_project(request.title, request.logline, request.target_format)
    return _project_response(project)


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: str) -> ProjectResponse:
    project = ProjectService().get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    return _project_response(project)

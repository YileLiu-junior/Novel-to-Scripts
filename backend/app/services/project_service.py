from __future__ import annotations

from uuid import uuid4

from app.domain.project import Project
from app.repositories.project_repository import ProjectRepository

# ProjectService owns the API-facing project use cases for V0+V1. It creates
# stable local project records and keeps routes from touching repository files.


class ProjectService:
    def __init__(self, repository: ProjectRepository | None = None) -> None:
        self.repository = repository or ProjectRepository()

    def create_project(self, title: str, logline: str | None = None, target_format: str = "web_series", project_id: str | None = None) -> Project:
        project = Project(
            id=project_id or f"project_{uuid4().hex[:12]}",
            title=title,
            logline=logline,
            target_format=target_format,
        )
        return self.repository.save(project)

    def get_project(self, project_id: str) -> Project | None:
        return self.repository.get(project_id)

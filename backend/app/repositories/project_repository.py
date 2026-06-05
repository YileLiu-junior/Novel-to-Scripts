from __future__ import annotations

from app.domain.project import Project


class ProjectRepository:
    def save(self, project: Project) -> Project:
        return project

    def get(self, project_id: str) -> Project | None:
        return None


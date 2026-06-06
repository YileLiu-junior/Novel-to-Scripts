from __future__ import annotations

from pathlib import Path

from app.domain.project import Project
from app.repositories.file_store import default_data_root, read_json, write_json_atomic


class ProjectRepository:
    def __init__(self, data_root: Path | None = None) -> None:
        self.data_root = data_root or default_data_root()
        self.projects_path = self.data_root / "projects.json"

    def save(self, project: Project) -> Project:
        records = read_json(self.projects_path, {})
        records[project.id] = project.model_dump(mode="json")
        write_json_atomic(self.projects_path, records)
        return project

    def get(self, project_id: str) -> Project | None:
        records = read_json(self.projects_path, {})
        data = records.get(project_id)
        if data is None:
            return None
        return Project.model_validate(data)

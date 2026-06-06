from __future__ import annotations

from pathlib import Path

from app.domain.project import Project
<<<<<<< HEAD
from app.repositories.file_store import default_data_root, read_json, write_json_atomic
=======
from app.repositories.file_store import default_data_root, ensure_directory, read_json, write_json_atomic
>>>>>>> 7be98a4 (feat: add screenplay schema design and JSON/YAML definitions)


class ProjectRepository:
    def __init__(self, data_root: Path | None = None) -> None:
        self.data_root = data_root or default_data_root()
        self.projects_path = self.data_root / "projects.json"

<<<<<<< HEAD
    def save(self, project: Project) -> Project:
=======
    def _project_dir(self, project_id: str) -> Path:
        return self.data_root / "projects" / project_id

    def _project_path(self, project_id: str) -> Path:
        return self._project_dir(project_id) / "project.json"

    def save(self, project: Project) -> Project:
        ensure_directory(self._project_dir(project.id))
        write_json_atomic(self._project_path(project.id), project.model_dump(mode="json"))
        # 兼容旧首页/脚本按 projects.json 查找项目的路径，同时新的运行时
        # 以 projects/{project_id}/project.json 为主。
>>>>>>> 7be98a4 (feat: add screenplay schema design and JSON/YAML definitions)
        records = read_json(self.projects_path, {})
        records[project.id] = project.model_dump(mode="json")
        write_json_atomic(self.projects_path, records)
        return project

    def get(self, project_id: str) -> Project | None:
<<<<<<< HEAD
=======
        project_path = self._project_path(project_id)
        if project_path.exists():
            return Project.model_validate(read_json(project_path, {}))
>>>>>>> 7be98a4 (feat: add screenplay schema design and JSON/YAML definitions)
        records = read_json(self.projects_path, {})
        data = records.get(project_id)
        if data is None:
            return None
        return Project.model_validate(data)

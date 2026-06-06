from __future__ import annotations

from pathlib import Path

from app.domain.source import Chapter
from app.repositories.file_store import default_data_root, read_json, write_json_atomic


class ChapterRepository:
    def __init__(self, data_root: Path | None = None) -> None:
        self.data_root = data_root or default_data_root()

    def _path_for(self, project_id: str) -> Path:
<<<<<<< HEAD
=======
        return self.data_root / "projects" / project_id / "chapters" / "index.json"

    def _legacy_path_for(self, project_id: str) -> Path:
>>>>>>> 7be98a4 (feat: add screenplay schema design and JSON/YAML definitions)
        return self.data_root / "projects" / project_id / "chapters.json"

    def replace_for_project(self, project_id: str, chapters: list[Chapter]) -> list[Chapter]:
        data = [chapter.model_dump(mode="json") for chapter in chapters]
        write_json_atomic(self._path_for(project_id), data)
        return chapters

    def list_for_project(self, project_id: str) -> list[Chapter]:
<<<<<<< HEAD
        records = read_json(self._path_for(project_id), [])
=======
        path = self._path_for(project_id)
        records = read_json(path, read_json(self._legacy_path_for(project_id), []))
>>>>>>> 7be98a4 (feat: add screenplay schema design and JSON/YAML definitions)
        return [Chapter.model_validate(record) for record in records]

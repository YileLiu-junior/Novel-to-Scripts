from __future__ import annotations

from pathlib import Path

from app.domain.source import Chapter
from app.repositories.file_store import default_data_root, read_json, write_json_atomic


class ChapterRepository:
    def __init__(self, data_root: Path | None = None) -> None:
        self.data_root = data_root or default_data_root()

    def _path_for(self, project_id: str) -> Path:
        return self.data_root / "projects" / project_id / "chapters.json"

    def replace_for_project(self, project_id: str, chapters: list[Chapter]) -> list[Chapter]:
        data = [chapter.model_dump(mode="json") for chapter in chapters]
        write_json_atomic(self._path_for(project_id), data)
        return chapters

    def list_for_project(self, project_id: str) -> list[Chapter]:
        records = read_json(self._path_for(project_id), [])
        return [Chapter.model_validate(record) for record in records]

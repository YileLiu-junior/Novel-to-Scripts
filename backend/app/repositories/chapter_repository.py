from __future__ import annotations

from app.domain.source import Chapter


class ChapterRepository:
    def replace_for_project(self, project_id: str, chapters: list[Chapter]) -> list[Chapter]:
        return chapters

    def list_for_project(self, project_id: str) -> list[Chapter]:
        return []


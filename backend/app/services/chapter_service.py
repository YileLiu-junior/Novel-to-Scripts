from __future__ import annotations

from app.core.ids import chapter_id, paragraph_id
from app.domain.source import Chapter, Paragraph
from app.repositories.chapter_repository import ChapterRepository
from app.validators.chapter_validator import ChapterValidator


class ChapterService:
    def __init__(
        self,
        repository: ChapterRepository | None = None,
        validator: ChapterValidator | None = None,
    ) -> None:
        self.repository = repository or ChapterRepository()
        self.validator = validator or ChapterValidator()

    def normalize_chapters(self, raw_chapters: list[dict[str, str]]) -> list[Chapter]:
        chapters: list[Chapter] = []
        for chapter_index, raw in enumerate(raw_chapters, start=1):
            text = raw.get("text", "")
            paragraphs = [
                Paragraph(id=paragraph_id(index), order=index, text=part.strip())
                for index, part in enumerate(text.split("\n\n"), start=1)
                if part.strip()
            ]
            chapters.append(
                Chapter(
                    id=chapter_id(chapter_index),
                    order=chapter_index,
                    title=raw.get("title") or f"Chapter {chapter_index}",
                    text=text,
                    paragraphs=paragraphs,
                )
            )
        return chapters

    def validate_generation_ready(self, chapters: list[Chapter]):
        return self.validator.validate_generation_ready(chapters)

    def replace_for_project(self, project_id: str, raw_chapters: list[dict[str, str]]) -> list[Chapter]:
        chapters = self.normalize_chapters(raw_chapters)
        return self.repository.replace_for_project(project_id, chapters)

    def list_for_project(self, project_id: str) -> list[Chapter]:
        return self.repository.list_for_project(project_id)

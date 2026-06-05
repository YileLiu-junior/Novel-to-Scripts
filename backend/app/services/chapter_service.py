from __future__ import annotations

from app.core.ids import chapter_id, paragraph_id
from app.domain.source import Chapter, Paragraph
from app.validators.chapter_validator import ChapterValidator


class ChapterService:
    def __init__(self, validator: ChapterValidator | None = None) -> None:
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


from __future__ import annotations

from app.domain.common import ValidationFinding
from app.domain.source import Chapter


class ChapterValidator:
    def validate_generation_ready(self, chapters: list[Chapter]) -> list[ValidationFinding]:
        findings: list[ValidationFinding] = []
        if len(chapters) < 3:
            findings.append(
                ValidationFinding(
                    code="chapters.too_few",
                    severity="error",
                    message="At least three chapters are required before generation.",
                    target_type="project",
                )
            )
        for chapter in chapters:
            if not chapter.text.strip():
                findings.append(
                    ValidationFinding(
                        code="chapter.empty_text",
                        severity="error",
                        message=f"Chapter {chapter.id} has empty text.",
                        target_type="chapter",
                        target_id=chapter.id,
                    )
                )
        return findings


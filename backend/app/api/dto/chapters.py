from __future__ import annotations

from pydantic import BaseModel, Field


class ChapterInput(BaseModel):
    title: str
    text: str


class ReplaceChaptersRequest(BaseModel):
    chapters: list[ChapterInput]


class ParagraphResponse(BaseModel):
    id: str
    order: int
<<<<<<< HEAD
=======
    text: str | None = None
>>>>>>> 7be98a4 (feat: add screenplay schema design and JSON/YAML definitions)
    summary: str | None = None


class ChapterResponse(BaseModel):
    id: str
    order: int
    title: str
<<<<<<< HEAD
=======
    text: str | None = None
    word_count: int = 0
>>>>>>> 7be98a4 (feat: add screenplay schema design and JSON/YAML definitions)
    paragraphs: list[ParagraphResponse] = []


# ---------------------------------------------------------------------------
# 自动拆章
# ---------------------------------------------------------------------------

class AutoSplitRequest(BaseModel):
    text: str = Field(..., min_length=1, description="原始全文文本")
    mode: str = Field(default="auto", description="拆分模式: rule / ai / auto")


class AutoSplitResponse(BaseModel):
    chapters: list[ChapterInput]
    chapter_count: int
    mode_used: str
<<<<<<< HEAD

=======
>>>>>>> 7be98a4 (feat: add screenplay schema design and JSON/YAML definitions)

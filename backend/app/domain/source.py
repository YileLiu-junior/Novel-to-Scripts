from __future__ import annotations

from pydantic import BaseModel, Field

## 源素材 小说原文

#Chapter → [Paragraph]
#  Chapter 持有 source_file（原文章节文件）、Paragraph 持有 text + summary。这是原始输入层。

class Paragraph(BaseModel):
    id: str
    order: int
    text: str | None = None
    summary: str | None = None


class Chapter(BaseModel):
    id: str
    order: int
    title: str
    text: str
    source_file: str | None = None
    source_anchor: str | None = None
    paragraphs: list[Paragraph] = Field(default_factory=list)


class ChapterSet(BaseModel):
    chapters: list[Chapter]


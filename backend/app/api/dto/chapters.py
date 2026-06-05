from pydantic import BaseModel


class ChapterInput(BaseModel):
    title: str
    text: str


class ReplaceChaptersRequest(BaseModel):
    chapters: list[ChapterInput]


class ParagraphResponse(BaseModel):
    id: str
    order: int
    summary: str | None = None


class ChapterResponse(BaseModel):
    id: str
    order: int
    title: str
    paragraphs: list[ParagraphResponse] = []


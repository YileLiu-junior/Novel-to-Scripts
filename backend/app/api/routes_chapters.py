from fastapi import APIRouter

from app.api.dto.chapters import ChapterResponse, ReplaceChaptersRequest
from app.services.chapter_service import ChapterService

router = APIRouter()


@router.put("/{project_id}/chapters", response_model=list[ChapterResponse])
def replace_chapters(project_id: str, request: ReplaceChaptersRequest) -> list[ChapterResponse]:
    chapters = ChapterService().normalize_chapters([item.model_dump() for item in request.chapters])
    return [
        ChapterResponse(
            id=chapter.id,
            order=chapter.order,
            title=chapter.title,
            paragraphs=[
                {"id": paragraph.id, "order": paragraph.order, "summary": paragraph.summary}
                for paragraph in chapter.paragraphs
            ],
        )
        for chapter in chapters
    ]


@router.get("/{project_id}/chapters", response_model=list[ChapterResponse])
def list_chapters(project_id: str) -> list[ChapterResponse]:
    return []


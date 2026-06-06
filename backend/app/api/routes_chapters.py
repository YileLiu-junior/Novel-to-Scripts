from fastapi import APIRouter, HTTPException

from app.api.dto.chapters import AutoSplitRequest, AutoSplitResponse, ChapterResponse, ReplaceChaptersRequest
from app.domain.source import Chapter
from app.services.chapter_service import ChapterService
from app.services.chapter_splitter import ChapterSplitter
from app.services.project_service import ProjectService

router = APIRouter()


def _chapter_response(chapter: Chapter) -> ChapterResponse:
    return ChapterResponse(
        id=chapter.id,
        order=chapter.order,
        title=chapter.title,
<<<<<<< HEAD
        paragraphs=[
            {"id": paragraph.id, "order": paragraph.order, "summary": paragraph.summary}
=======
        text=chapter.text,
        word_count=len(chapter.text or ""),
        paragraphs=[
            {"id": paragraph.id, "order": paragraph.order, "text": paragraph.text, "summary": paragraph.summary}
>>>>>>> 7be98a4 (feat: add screenplay schema design and JSON/YAML definitions)
            for paragraph in chapter.paragraphs
        ],
    )


@router.put("/{project_id}/chapters", response_model=list[ChapterResponse])
def replace_chapters(project_id: str, request: ReplaceChaptersRequest) -> list[ChapterResponse]:
    if ProjectService().get_project(project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    chapters = ChapterService().replace_for_project(project_id, [item.model_dump() for item in request.chapters])
    return [_chapter_response(chapter) for chapter in chapters]


@router.get("/{project_id}/chapters", response_model=list[ChapterResponse])
def list_chapters(project_id: str) -> list[ChapterResponse]:
    if ProjectService().get_project(project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    return [_chapter_response(chapter) for chapter in ChapterService().list_for_project(project_id)]


@router.post("/{project_id}/chapters/auto-split", response_model=AutoSplitResponse)
def auto_split_chapters(project_id: str, request: AutoSplitRequest) -> AutoSplitResponse:
    """将原始全文文本自动拆分为章节并持久化。"""
    if ProjectService().get_project(project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    splitter = ChapterSplitter()
    split_chapters = splitter.split(request.text, mode=request.mode)

    # 持久化到项目
    chapters = ChapterService().replace_for_project(
        project_id,
        [ch.to_dict() for ch in split_chapters],
    )

    return AutoSplitResponse(
        chapters=[{"title": ch.title, "text": ch.text} for ch in chapters],
        chapter_count=len(chapters),
        mode_used="rule" if len(split_chapters) >= 2 else "ai",
    )

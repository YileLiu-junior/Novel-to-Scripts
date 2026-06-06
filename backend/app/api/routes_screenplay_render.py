"""Screenplay render API — 文学剧本可读预览与下载。"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Response

from app.api.dto.screenplay_render import RenderedPreviewResponse
from app.services.project_service import ProjectService
from app.services.screenplay_render_service import ScreenplayRenderService

router = APIRouter()


def _get_rendered_or_404(project_id: str):
    """获取最新 screenlay_rendered artifact (Pydantic Artifact)，不存在则 404。"""
    if ProjectService().get_project(project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    service = ScreenplayRenderService()
    rendered = service.get_latest_rendered(project_id)
    if rendered is None:
        raise HTTPException(
            status_code=404,
            detail="No screenlay_rendered artifact. Run generation first.",
        )
    return rendered


@router.get("/{project_id}/screenplay/rendered", response_model=RenderedPreviewResponse)
def preview_rendered(
    project_id: str,
    format: str = Query("markdown", description="渲染格式: markdown 或 text"),
) -> RenderedPreviewResponse:
    """预览渲染后的文学剧本文本。"""
    if format not in ("markdown", "text"):
        raise HTTPException(status_code=400, detail=f"Unsupported format: {format}. Use 'markdown' or 'text'.")

    rendered = _get_rendered_or_404(project_id)
    fmt = ScreenplayRenderService.extract_format(rendered, format)
    if fmt is None:
        raise HTTPException(status_code=500, detail=f"Format '{format}' not found in rendered artifact.")

    data = rendered.data
    if isinstance(data, str):
        raise HTTPException(status_code=500, detail="Rendered artifact data is malformed.")

    return RenderedPreviewResponse(
        format=format,
        content=fmt.get("content", ""),
        filename=fmt.get("filename", f"screenplay.{'md' if format == 'markdown' else 'txt'}"),
        media_type=fmt.get("media_type", "text/plain"),
        artifact_id=rendered.id,
        source_artifact_id=data.get("source_artifact_id", ""),
    )


@router.get("/{project_id}/screenplay/rendered/download")
def download_rendered(
    project_id: str,
    format: str = Query("markdown", description="渲染格式: markdown 或 text"),
) -> Response:
    """下载渲染后的文学剧本文件。"""
    if format not in ("markdown", "text"):
        raise HTTPException(status_code=400, detail=f"Unsupported format: {format}. Use 'markdown' or 'text'.")

    rendered = _get_rendered_or_404(project_id)
    fmt = ScreenplayRenderService.extract_format(rendered, format)
    if fmt is None:
        raise HTTPException(status_code=500, detail=f"Format '{format}' not found in rendered artifact.")

    return Response(
        content=fmt.get("content", ""),
        media_type=fmt.get("media_type", "text/plain; charset=utf-8"),
        headers={
            "Content-Disposition": f'attachment; filename="{fmt.get("filename", "screenplay.txt")}"',
        },
    )

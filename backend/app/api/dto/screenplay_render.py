"""Screenplay render DTOs."""

from __future__ import annotations

from pydantic import BaseModel, Field


class RenderedPreviewResponse(BaseModel):
    format: str = Field(..., description="markdown 或 text")
    content: str = Field(..., description="渲染后的文本内容")
    filename: str = Field(..., description="建议下载文件名")
    media_type: str = Field(..., description="MIME 类型")
    artifact_id: str = Field(..., description="screenplay_rendered artifact ID")
    source_artifact_id: str = Field(..., description="screenplay_json artifact ID")

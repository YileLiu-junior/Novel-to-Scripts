from __future__ import annotations

from typing import Any

from app.ai.providers.factory import build_ai_provider
from app.ai.skills.chapter_boundary_reader import ChapterBoundaryReaderSkill
from app.domain.source import Chapter
from app.services.artifact_service import ArtifactService
from app.services.chapter_service import ChapterService
from app.services.chapter_splitter import ChapterSplitter


class ChapterIntakeService:
    """章节导入编排：拆分 raw txt、保存章节、记录 boundary trace。"""

    def __init__(
        self,
        chapter_service: ChapterService | None = None,
        artifact_service: ArtifactService | None = None,
        provider: Any | None = None,
    ) -> None:
        self.chapter_service = chapter_service or ChapterService()
        self.artifact_service = artifact_service or ArtifactService()
        self.provider = provider

    def auto_split_and_save(self, project_id: str, text: str, mode: str = "auto") -> tuple[list[Chapter], dict[str, Any]]:
        """执行自动拆章并持久化章节，trace 作为 artifact 保存供调试。"""
        boundary_reader = _LazyChapterBoundaryReader(self.provider)
        split_result = ChapterSplitter(boundary_reader=boundary_reader).split_with_trace(text, mode=mode)
        chapters = self.chapter_service.replace_for_project(
            project_id,
            [chapter.to_dict() for chapter in split_result.chapters],
        )
        trace = split_result.trace()
        if split_result.mode_used == "ai" or trace["ignored_spans"] or trace["warnings"]:
            self.artifact_service.save_artifact(project_id, "chapter_split_plan", trace)
        return chapters, trace


class _LazyChapterBoundaryReader:
    """只在规则拆分失败进入 AI fallback 时构造真实 provider。"""

    def __init__(self, provider: Any | None = None) -> None:
        self.provider = provider

    def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        provider = self.provider or build_ai_provider()
        return ChapterBoundaryReaderSkill(provider).run(input_data)

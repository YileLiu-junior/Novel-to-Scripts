"""Screenplay render service — 编排校验 + 渲染 + 持久化为 artifact。"""

from __future__ import annotations

from typing import Any

from app.domain.artifacts import Artifact
from app.exporters.screenplay_render_exporter import ScreenplayRenderExporter
from app.services.artifact_service import ArtifactService
from app.services.validation_service import ValidationService


class ScreenplayRenderService:
    def __init__(
        self,
        validation_service: ValidationService | None = None,
        artifact_service: ArtifactService | None = None,
    ) -> None:
        self.validation_service = validation_service or ValidationService()
        self.artifact_service = artifact_service or ArtifactService()
        self.exporter = ScreenplayRenderExporter()

    # ------------------------------------------------------------------
    # 生成并保存
    # ------------------------------------------------------------------

    def render_and_save(
        self,
        project_id: str,
        screenplay_json: dict[str, Any],
        job_id: str | None = None,
    ) -> Artifact:
        """校验 → 渲染 → 持久化为 screenlay_rendered artifact。"""
        # 校验
        findings = self.validation_service.validate_screenplay(screenplay_json)
        errors = [f for f in findings if f.severity == "error"]
        if errors:
            raise ValueError(f"Cannot render invalid screenplay: {errors[0].message}")

        # 渲染两种格式
        markdown = self.exporter.render_markdown(screenplay_json)
        text = self.exporter.render_text(screenplay_json)

        # 查找源 screenplay_json artifact
        source = self._find_latest_screenplay_json(project_id)

        # 构建 artifact data
        rendered: dict[str, Any] = {
            "render_version": "1.0",
            "source_artifact_type": "screenplay_json",
            "source_artifact_id": source.id if source else "",
            "formats": {
                "markdown": {
                    "filename": "demo_screenplay.md",
                    "media_type": self.exporter.MARKDOWN_MEDIA_TYPE,
                    "content": markdown,
                },
                "text": {
                    "filename": "demo_screenplay.txt",
                    "media_type": self.exporter.TEXT_MEDIA_TYPE,
                    "content": text,
                },
            },
        }

        # 持久化
        return self.artifact_service.save_artifact(
            project_id, "screenplay_rendered", rendered, job_id
        )

    # ------------------------------------------------------------------
    # 查询已有
    # ------------------------------------------------------------------

    def get_latest_rendered(self, project_id: str) -> Artifact | None:
        """获取最新的 screenlay_rendered artifact (Pydantic model)。"""
        return self.artifact_service.latest_for_project(project_id, "screenplay_rendered")

    @staticmethod
    def extract_format(
        artifact: Artifact,
        format_: str,
    ) -> dict[str, Any] | None:
        """从 rendered artifact 中提取指定格式的数据。"""
        data = artifact.data
        if isinstance(data, str):
            return None
        formats = data.get("formats", {})
        return formats.get(format_)

    # ------------------------------------------------------------------
    # 内部
    # ------------------------------------------------------------------

    def _find_latest_screenplay_json(self, project_id: str) -> Artifact | None:
        return self.artifact_service.latest_for_project(project_id, "screenplay_json")

"""Screenplay render service — 编排校验 + 渲染 + 持久化为 artifact + 导出 .md/.txt 文件。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.domain.artifacts import Artifact
from app.exporters.screenplay_render_exporter import ScreenplayRenderExporter
from app.repositories.file_store import default_data_root
from app.services.artifact_service import ArtifactService
from app.services.validation_service import ValidationService
from app.validators.screenplay_normalizer import normalize_screenplay_for_export


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
        """校验 → 渲染 → 持久化为 artifact + 导出 .md / .txt 文件到 artifacts 目录。"""
        screenplay_json = normalize_screenplay_for_export(screenplay_json)
        # 校验
        findings = self.validation_service.validate_screenplay(screenplay_json)
        errors = [f for f in findings if f.severity == "error"]
        if errors:
            first = errors[0]
            raise ValueError(
                "Cannot render invalid screenplay: "
                f"{first.message}; path={first.path or '<root>'}; "
                f"schema_path={first.schema_path or '<schema-root>'}"
            )

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
                    "filename": "screenplay.md",
                    "media_type": self.exporter.MARKDOWN_MEDIA_TYPE,
                    "content": markdown,
                },
                "text": {
                    "filename": "screenplay.txt",
                    "media_type": self.exporter.TEXT_MEDIA_TYPE,
                    "content": text,
                },
            },
        }

        # 同时导出独立的 .md 和 .txt 文件到 artifacts 目录
        self._write_standalone_files(project_id, markdown, text)

        # 持久化
        return self.artifact_service.save_artifact(
            project_id, "screenplay_rendered", rendered, job_id
        )

    # ------------------------------------------------------------------
    # 独立文件导出
    # ------------------------------------------------------------------

    @staticmethod
    def _write_standalone_files(
        project_id: str, markdown: str, text: str
    ) -> None:
        """在项目 artifacts 目录写出 screenplay.md 和 screenplay.txt。"""
        artifacts_dir = default_data_root() / "projects" / project_id / "artifacts"
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        (artifacts_dir / "screenplay.md").write_text(markdown, encoding="utf-8")
        (artifacts_dir / "screenplay.txt").write_text(text, encoding="utf-8")

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

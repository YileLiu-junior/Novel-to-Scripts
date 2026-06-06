"""
screenplay_preview.py
独立的"文学剧本预览"页面。

优先使用 project/session_state 中的 rendered_markdown 缓存；
如果没有则调用 api_client.get_rendered() 从后端实时获取。
支持 Markdown / TXT 两种格式下载。
"""

from __future__ import annotations

from typing import Any

import streamlit as st

from frontend import api_client


def _get_backend_project_id(project: dict) -> str | None:
    """从 project 或 session_state 中获取后端项目 ID。"""
    return project.get("backend_project_id") or st.session_state.get("backend_project_id")


def _get_rendered_markdown(project: dict) -> str:
    """获取文学剧本的 Markdown 文本，优先使用缓存，其次调用后端接口。"""
    # 优先从 project / session_state 缓存中读取
    markdown_text = (
        project.get("rendered_markdown")
        or st.session_state.get("rendered_markdown")
        or ""
    )
    if markdown_text:
        return markdown_text

    # 缓存为空，尝试从后端实时获取
    project_id = _get_backend_project_id(project)
    if not project_id:
        return ""

    try:
        rendered = api_client.get_rendered(project_id, "markdown")
        markdown_text = rendered.get("content", "")
    except api_client.ApiClientError:
        # 回退：尝试从 screenplay_rendered artifact 中提取
        rendered_artifact = project.get("screenplay_rendered")
        if isinstance(rendered_artifact, dict):
            markdown_text = (
                rendered_artifact
                .get("formats", {})
                .get("markdown", {})
                .get("content", "")
            )

    return markdown_text


def _download_button(label: str, project_id: str, format_name: str) -> None:
    """封装下载按钮，处理下载异常。"""
    try:
        file_data = api_client.download_rendered(project_id, format_name)
        st.download_button(
            label=label,
            data=file_data.content,
            file_name=file_data.filename,
            mime=file_data.media_type,
            use_container_width=True,
        )
    except api_client.ApiClientError as exc:
        st.warning(f"下载暂不可用：{exc.message}")


def render(project: dict):
    """渲染文学剧本预览页面。"""
    st.header("📝 文学剧本预览")
    st.caption("查看并下载后端生成的文学剧本。")
    st.markdown("---")

    # 显示当前项目名称
    project_name = project.get("name", "未命名项目")
    st.subheader(f"项目：{project_name}")

    # 获取后端项目 ID
    project_id = _get_backend_project_id(project)

    # 获取 Markdown 内容
    try:
        markdown_text = _get_rendered_markdown(project)
    except Exception:
        st.warning("无法连接后端服务，请确认 FastAPI 已启动。")
        return

    # 渲染 Markdown 内容
    if markdown_text:
        st.markdown(markdown_text)
    else:
        job_status = project.get("backend_job_status", "idle")
        if job_status == "succeeded":
            st.info("生成已完成，但暂无文学剧本内容。")
        elif job_status in ("queued", "running"):
            st.info("剧本正在生成中，请稍后再来查看文学剧本。")
        else:
            st.info("暂无文学剧本。请先在「原文管理」页面导入原文并点击「开始生成结构化剧本」")

    # 下载按钮区域
    if project_id:
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            _download_button("下载 Markdown", project_id, "markdown")
        with col2:
            _download_button("下载 TXT", project_id, "text")

# -*- coding: utf-8 -*-
"""
data_loader.py
共享数据加载工具函数。

多个页面（人物管理、场景管理、情节、审查报告）都需要从后端加载
screenplay_json / screenplay_yaml / rendered_markdown 等数据。
本模块将这些重复的加载逻辑统一封装，避免各页面各自请求。

设计原则：
- 优先从 project dict 或 session_state 中读取缓存；
- 仅在缓存为空且存在 backend_project_id 时才发起 HTTP 请求；
- 所有函数不抛异常，出错时返回空值并静默处理；
- 拉取成功后同步更新 project dict 和 session_state。
"""

from __future__ import annotations

import logging
from typing import Any

import streamlit as st

from frontend import api_client
from frontend.utils import storage
from frontend.utils.screenplay_local_store import merge_with_local

logger = logging.getLogger(__name__)


def get_backend_project_id(project: dict) -> str | None:
    """
    从 project dict 或 session_state 中获取 backend_project_id。

    优先读取 project dict 中的值，若为空则回退到 session_state。
    """
    pid = project.get("backend_project_id")
    if pid:
        return pid
    # 回退到 session_state
    return getattr(st.session_state, "backend_project_id", None)


def load_screenplay_data(project: dict) -> dict[str, Any]:
    """
    加载 screenplay_data（screenplay_json）。

    1. 先检查 project dict 中是否已有 screenplay_data；
    2. 若为空，再检查 session_state；
    3. 仍为空且有 backend_project_id 时，从后端 API 拉取；
    4. 拉取成功后通过 storage.update_project 写入持久化并同步 session_state；
    5. 出错时返回空 dict，不抛异常。
    """
    # 优先从 project 缓存读取
    data = project.get("screenplay_data")
    if isinstance(data, dict) and data:
        return data

    # 回退到 session_state
    ss_data = getattr(st.session_state, "screenplay_data", None)
    if isinstance(ss_data, dict) and ss_data:
        return ss_data

    # 尝试从后端拉取
    backend_pid = get_backend_project_id(project)
    if not backend_pid:
        return {}

    try:
        artifact = api_client.get_artifact(backend_pid, "screenplay_json")
        # artifact 结构可能是 {"data": {...}} 或直接就是数据
        if isinstance(artifact, dict):
            fetched = artifact.get("data", artifact)
        else:
            fetched = artifact

        if not isinstance(fetched, dict):
            return {}

        # 同步到 session_state
        st.session_state.screenplay_data = fetched

        # 同步到持久化存储
        project_id = project.get("id")
        if project_id:
            storage.update_project(project_id, {"screenplay_data": fetched})

        # 与本地编辑数据合并（本地编辑优先级更高）
        return merge_with_local(project_id, fetched)
    except Exception as exc:
        logger.warning("加载 screenplay_data 失败: %s", exc)
        return {}


def load_screenplay_yaml(project: dict) -> str:
    """
    加载 screenplay_yaml 文本。

    逻辑与 load_screenplay_data 一致，区别在于：
    - 缓存字段为 screenplay_yaml（字符串类型）；
    - 从后端拉取时使用 download_yaml 接口并解码为文本。
    """
    # 优先从 project 缓存读取
    yaml_text = project.get("screenplay_yaml")
    if isinstance(yaml_text, str) and yaml_text:
        return yaml_text

    # 回退到 session_state
    ss_yaml = getattr(st.session_state, "screenplay_yaml", None)
    if isinstance(ss_yaml, str) and ss_yaml:
        return ss_yaml

    # 尝试从后端拉取
    backend_pid = get_backend_project_id(project)
    if not backend_pid:
        return ""

    try:
        downloaded = api_client.download_yaml(backend_pid)
        yaml_text = downloaded.content.decode("utf-8", errors="ignore")

        if not yaml_text:
            return ""

        # 同步到 session_state
        st.session_state.screenplay_yaml = yaml_text

        # 同步到持久化存储
        project_id = project.get("id")
        if project_id:
            storage.update_project(project_id, {"screenplay_yaml": yaml_text})

        return yaml_text
    except Exception as exc:
        logger.warning("加载 screenplay_yaml 失败: %s", exc)
        return ""


def load_rendered_markdown(project: dict) -> str:
    """
    加载渲染后的 markdown 文本。

    逻辑与 load_screenplay_data 一致，区别在于：
    - 缓存字段为 rendered_markdown（字符串类型）；
    - 从后端拉取时使用 get_rendered 接口并提取文本内容。
    """
    # 优先从 project 缓存读取
    md_text = project.get("rendered_markdown")
    if isinstance(md_text, str) and md_text:
        return md_text

    # 回退到 session_state
    ss_md = getattr(st.session_state, "rendered_markdown", None)
    if isinstance(ss_md, str) and ss_md:
        return ss_md

    # 尝试从后端拉取
    backend_pid = get_backend_project_id(project)
    if not backend_pid:
        return ""

    try:
        result = api_client.get_rendered(backend_pid, "markdown")
        # get_rendered 返回 dict，文本内容通常在 "content" 或 "text" 字段中
        if isinstance(result, dict):
            md_text = result.get("content") or result.get("text") or ""
        elif isinstance(result, str):
            md_text = result
        else:
            md_text = ""

        if not md_text:
            return ""

        # 同步到 session_state
        st.session_state.rendered_markdown = md_text

        # 同步到持久化存储
        project_id = project.get("id")
        if project_id:
            storage.update_project(project_id, {"rendered_markdown": md_text})

        return md_text
    except Exception as exc:
        logger.warning("加载 rendered_markdown 失败: %s", exc)
        return ""


def refresh_all_artifacts(project: dict) -> dict:
    """
    一次性拉取 screenplay_json、screenplay_yaml、rendered_markdown 三类制品。

    无论本地缓存是否已有数据，都会向后端发起请求以获取最新版本。
    拉取成功后同步更新 project dict 和 session_state。
    返回更新后的 project dict（原地修改传入的 project 并返回）。
    """
    backend_pid = get_backend_project_id(project)
    if not backend_pid:
        return project

    updates: dict[str, Any] = {}

    # 拉取 screenplay_json
    try:
        artifact = api_client.get_artifact(backend_pid, "screenplay_json")
        if isinstance(artifact, dict):
            fetched = artifact.get("data", artifact)
            if isinstance(fetched, dict):
                updates["screenplay_data"] = fetched
                st.session_state.screenplay_data = fetched
    except Exception as exc:
        logger.warning("refresh_all_artifacts: 加载 screenplay_data 失败: %s", exc)

    # 拉取 screenplay_yaml
    try:
        downloaded = api_client.download_yaml(backend_pid)
        yaml_text = downloaded.content.decode("utf-8", errors="ignore")
        if yaml_text:
            updates["screenplay_yaml"] = yaml_text
            st.session_state.screenplay_yaml = yaml_text
    except Exception as exc:
        logger.warning("refresh_all_artifacts: 加载 screenplay_yaml 失败: %s", exc)

    # 拉取 rendered_markdown
    try:
        result = api_client.get_rendered(backend_pid, "markdown")
        md_text = ""
        if isinstance(result, dict):
            md_text = result.get("content") or result.get("text") or ""
        elif isinstance(result, str):
            md_text = result
        if md_text:
            updates["rendered_markdown"] = md_text
            st.session_state.rendered_markdown = md_text
    except Exception as exc:
        logger.warning("refresh_all_artifacts: 加载 rendered_markdown 失败: %s", exc)

    # 批量写入持久化存储
    if updates:
        project_id = project.get("id")
        if project_id:
            # 与本地编辑数据合并（本地编辑优先级更高）
            if "screenplay_data" in updates:
                updates["screenplay_data"] = merge_with_local(project_id, updates["screenplay_data"])
            updated = storage.update_project(project_id, updates)
            if updated:
                # 用持久化后的最新数据覆盖传入的 project
                project.update(updated)

    return project

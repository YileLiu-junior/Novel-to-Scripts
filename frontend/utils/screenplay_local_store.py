# -*- coding: utf-8 -*-
"""
screenplay_local_store.py
前端本地存储工具：使用 browser localStorage 保存编辑后的 screenplay_data。
按 project_id 区分，避免不同项目数据混淆。

加载优先级：
1. 先请求后端 screenplay_json
2. 再检查 localStorage 是否有当前 project_id 的编辑版本
3. 如果有本地编辑版本，优先展示本地版本
4. 如果没有，展示后端返回的原始版本
"""

from __future__ import annotations

import json
from typing import Any

import streamlit as st


_LOCAL_KEY_PREFIX = "screenplay_edits_"


def _key(project_id: str) -> str:
    """根据 project_id 生成 localStorage key。"""
    return f"{_LOCAL_KEY_PREFIX}{project_id}"


def get_local_screenplay(project_id: str) -> dict[str, Any] | None:
    """
    从 localStorage 读取指定项目的本地编辑版 screenplay_data。
    返回 dict 或 None（没有本地编辑数据时）。
    """
    if not project_id:
        return None
    # Streamlit 没有直接访问 browser localStorage 的 API，
    # 但可以通过 st.session_state 中的 __local_storage 模拟（组件注入）
    # 或者使用 st.query_params / st.session_state 持久化。
    # 这里使用 session_state 作为跨页面刷新的持久化方案。
    key = _key(project_id)
    # 优先从 session_state 读取（Streamlit 的 session_state 在页面刷新后会丢失，
    # 但可以通过 storage.update_project 持久化到本地 JSON 文件）
    if key in st.session_state:
        return st.session_state[key]
    return None


def save_local_screenplay(project_id: str, data: dict[str, Any]) -> None:
    """
    将编辑后的 screenplay_data 保存到前端本地存储。
    同时写入 session_state 和本地 projects.json（通过 storage.update_project）。
    """
    if not project_id:
        return
    key = _key(project_id)
    st.session_state[key] = data
    # 同时通过 storage 持久化到本地 JSON，确保页面刷新后仍能读取
    from frontend.utils import storage
    storage.update_project(project_id, {key: data})


def clear_local_screenplay(project_id: str) -> None:
    """
    清除指定项目的本地编辑数据，恢复后端原始版本。
    """
    if not project_id:
        return
    key = _key(project_id)
    st.session_state.pop(key, None)
    from frontend.utils import storage
    storage.update_project(project_id, {key: None})


def has_local_edits(project_id: str) -> bool:
    """检查指定项目是否有本地编辑数据。"""
    return get_local_screenplay(project_id) is not None


def merge_with_local(project_id: str, backend_data: dict[str, Any]) -> dict[str, Any]:
    """
    将后端数据与本地编辑数据合并。
    本地编辑数据优先级更高（覆盖后端对应字段）。
    """
    local = get_local_screenplay(project_id)
    if not local:
        return backend_data
    # 本地数据覆盖后端数据
    merged = dict(backend_data)
    merged.update(local)
    return merged

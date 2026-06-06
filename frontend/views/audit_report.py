"""
audit_report.py
独立的"审查报告"页面。

优先从 screenplay_data.audit_report 中读取审查数据；
如果没有则尝试调用 api_client.get_artifact() 从后端获取。
按四个分类以 expander 形式展示警告详情。
"""

from __future__ import annotations

from typing import Any

import streamlit as st

from frontend import api_client
from frontend import backend_types as bt


def _get_backend_project_id(project: dict) -> str | None:
    """从 project 或 session_state 中获取后端项目 ID。"""
    return project.get("backend_project_id") or st.session_state.get("backend_project_id")


def _get_screenplay_data(project: dict) -> dict[str, Any]:
    """从 project / session_state 中获取 screenplay_data。"""
    data = project.get("screenplay_data") or st.session_state.get("screenplay_data") or {}
    return data if isinstance(data, dict) else {}


def _get_audit_report(project: dict) -> dict[str, Any] | None:
    """获取审查报告数据，优先使用本地缓存，其次调用后端接口。"""
    # 优先从 screenplay_data.audit_report 获取
    screenplay_data = _get_screenplay_data(project)
    audit = screenplay_data.get("audit_report")
    if isinstance(audit, dict) and audit:
        return audit

    # 其次从 project / session_state 顶层获取
    audit = project.get("audit_report") or st.session_state.get("audit_report")
    if isinstance(audit, dict) and audit:
        return audit

    # 最后尝试从后端实时获取
    project_id = _get_backend_project_id(project)
    if not project_id:
        return None

    try:
        artifact = api_client.get_artifact(project_id, "audit_report")
        audit = artifact.get("data")
        if isinstance(audit, dict) and audit:
            return audit
    except api_client.ApiClientError:
        pass

    return None


def _format_warning_item(item: Any) -> str:
    """将单条警告格式化为可读文本。"""
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        parts = []
        # 提取常见字段
        message = item.get("message") or item.get("description") or item.get("detail") or ""
        if message:
            parts.append(str(message))
        location = item.get("location") or item.get("path") or item.get("field") or ""
        if location:
            parts.append(f"位置：{location}")
        severity = item.get("severity") or item.get("level") or ""
        if severity:
            parts.append(f"级别：{severity}")
        suggestion = item.get("suggestion") or item.get("fix") or ""
        if suggestion:
            parts.append(f"建议：{suggestion}")
        return " | ".join(parts) if parts else str(item)
    return str(item)


def _render_warning_category(label: str, items: list[Any]) -> None:
    """渲染单个警告分类的 expander 区域。"""
    with st.expander(f"{label}（{len(items)}）", expanded=bool(items)):
        if not items:
            st.caption("暂无问题")
            return
        for idx, item in enumerate(items, 1):
            st.markdown(f"**{idx}.** {_format_warning_item(item)}")


def render(project: dict):
    """渲染审查报告页面。"""
    st.header("📊 审查报告")
    st.caption("查看剧本生成后的审查结果与改进建议。")
    st.markdown("---")

    # 获取审查报告数据
    try:
        audit = _get_audit_report(project)
    except Exception:
        st.warning("无法连接后端服务，请确认 FastAPI 已启动。")
        return

    # 无审查报告时的提示
    if not audit:
        job_status = project.get("backend_job_status", "idle")
        if job_status == "succeeded":
            st.info("生成已完成，但暂无审查报告。")
        elif job_status in ("queued", "running"):
            st.info("剧本正在生成中，请稍后再来查看审查报告。")
        else:
            st.info("暂无审查报告。请先在「原文管理」页面导入原文并点击「开始生成结构化剧本」")
        return

    # 显示总问题数
    total = bt.warning_count(audit)
    if total == 0:
        st.success("审查通过，暂无问题。")
    else:
        st.warning(f"共发现 **{total}** 条审查提示。")

    # 四个分类展示
    categories = [
        ("schema_warnings", "Schema 警告"),
        ("continuity_warnings", "连贯性警告"),
        ("dialogue_warnings", "对白警告"),
        ("unresolved_foreshadowing", "未兑现伏笔"),
    ]

    for key, label in categories:
        items = bt.as_list(audit.get(key))
        _render_warning_category(label, items)

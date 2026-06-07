"""
editor.py
项目编辑页布局：左侧导航和右侧功能页面路由。
"""

import streamlit as st

from frontend.utils import state, storage
from frontend.views import audit_report, characters, export, original, plots, scenes


def _restore_backend_snapshot(project: dict) -> None:
    """把本地项目中保存的后端联调快照恢复到 session_state。"""
    for key in (
        "backend_project_id",
        "backend_chapters",
        "backend_job_id",
        "backend_job_status",
        "backend_current_step",
        "backend_error",
        "backend_artifacts",
        "screenplay_data",
        "screenplay_yaml",
        "rendered_markdown",
    ):
        if project.get(key) is not None:
            st.session_state[key] = project.get(key)


def _nav_button(label: str, section: str, current_section: str) -> None:
    """渲染一个侧边栏导航按钮，并在当前页面后添加选中标记。"""
    active_label = f"{label} ✓" if current_section == section else label
    if st.button(active_label, use_container_width=True):
        state.switch_section(section)


def render():
    """渲染项目编辑页面。"""
    project_id = st.session_state.get("current_project_id")
    if not project_id:
        state.go_home()
        return

    project = storage.get_project_by_id(project_id)
    if not project:
        st.error("项目不存在或已被删除，即将返回项目首页...")
        state.go_home()
        return

    _restore_backend_snapshot(project)

    st.title(f"{project.get('name', '未命名项目')}")
    st.markdown("---")

    with st.sidebar:
        st.markdown("## 导航")

        if st.button("返回项目首页", use_container_width=True):
            state.go_home()

        st.markdown("---")
        st.markdown(f"**当前项目：** {project.get('name', '未命名')}")
        st.markdown("---")

        current_section = st.session_state.get("current_section", "original")
        _nav_button("原文管理", "original", current_section)
        _nav_button("人物管理", "characters", current_section)
        _nav_button("场景管理", "scenes", current_section)
        _nav_button("事件管理", "plots", current_section)
        _nav_button("生成结果", "export", current_section)
        _nav_button("审查报告", "audit_report", current_section)

    current_section = st.session_state.get("current_section", "original")

    if current_section == "original":
        original.render(project)
    elif current_section == "characters":
        characters.render(project)
    elif current_section == "scenes":
        scenes.render(project)
    elif current_section == "plots":
        plots.render(project)
    elif current_section in {"export", "screenplay_preview"}:
        export.render(project)
    elif current_section == "audit_report":
        audit_report.render(project)
    else:
        st.error("未知页面，请重新选择导航项。")

"""
editor.py
项目编辑页面整体布局：左侧导航 + 右侧内容区。
根据 current_section 调用对应的子页面。
"""

import streamlit as st
from frontend.utils import storage, state
from frontend.views import original, characters, scenes, plots, screenplay_preview, export, audit_report


def render():
    """
    渲染项目编辑页面。
    左侧为导航栏，右侧为对应功能页面。
    """
    project_id = st.session_state.get("current_project_id")
    if not project_id:
        # 如果没有当前项目，回到首页
        state.go_home()
        return

    project = storage.get_project_by_id(project_id)
    if not project:
        st.error("项目不存在或已被删除，即将返回首页...")
        state.go_home()
        return

    # 将本地持久化的后端状态恢复到 session_state，刷新页面后仍能继续查看结果。
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

    # 页面标题使用项目名称
    st.title(f"🎬 {project.get('name', '未命名项目')}")
    st.markdown("---")

    # 左侧导航栏
    with st.sidebar:
        st.markdown("## 导航")

        if st.button("🏠 返回项目首页", use_container_width=True):
            state.go_home()

        st.markdown("---")
        st.markdown(f"**当前项目：** {project.get('name', '未命名')}")
        st.markdown("---")

        # 导航按钮：根据当前 section 高亮
        current_section = st.session_state.get("current_section", "original")

        btn_original_label = "📄 原文管理" if current_section != "original" else "📄 原文管理 ✓"
        if st.button(btn_original_label, use_container_width=True):
            state.switch_section("original")

        btn_characters_label = "👤 人物管理" if current_section != "characters" else "👤 人物管理 ✓"
        if st.button(btn_characters_label, use_container_width=True):
            state.switch_section("characters")

        btn_scenes_label = "🎭 场景管理" if current_section != "scenes" else "🎭 场景管理 ✓"
        if st.button(btn_scenes_label, use_container_width=True):
            state.switch_section("scenes")

        btn_plots_label = "📖 情节" if current_section != "plots" else "📖 情节 ✓"
        if st.button(btn_plots_label, use_container_width=True):
            state.switch_section("plots")

        btn_screenplay_preview_label = "📝 文学剧本预览" if current_section != "screenplay_preview" else "📝 文学剧本预览 ✓"
        if st.button(btn_screenplay_preview_label, use_container_width=True):
            state.switch_section("screenplay_preview")

        btn_export_label = "📋 生成结果" if current_section != "export" else "📋 生成结果 ✓"
        if st.button(btn_export_label, use_container_width=True):
            state.switch_section("export")

        btn_audit_report_label = "📊 审查报告" if current_section != "audit_report" else "📊 审查报告 ✓"
        if st.button(btn_audit_report_label, use_container_width=True):
            state.switch_section("audit_report")

    # 右侧主内容区
    current_section = st.session_state.get("current_section", "original")

    if current_section == "original":
        original.render(project)
    elif current_section == "characters":
        characters.render(project)
    elif current_section == "scenes":
        scenes.render(project)
    elif current_section == "plots":
        plots.render(project)
    elif current_section == "screenplay_preview":
        screenplay_preview.render(project)
    elif current_section == "export":
        export.render(project)
    elif current_section == "audit_report":
        audit_report.render(project)
    else:
        st.error("未知页面，请重新选择导航项。")

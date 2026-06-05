"""
editor.py
项目编辑页面整体布局：左侧导航 + 右侧内容区。
根据 current_section 调用对应的子页面。
"""

import streamlit as st
from frontend.utils import storage, state
from frontend.views import original, characters, scenes, acts, export


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

        btn_original_label = "📄 原文" if current_section != "original" else "📄 原文 ✓"
        if st.button(btn_original_label, use_container_width=True):
            state.switch_section("original")

        btn_characters_label = "👤 人物" if current_section != "characters" else "👤 人物 ✓"
        if st.button(btn_characters_label, use_container_width=True):
            state.switch_section("characters")

        btn_scenes_label = "🎭 场景" if current_section != "scenes" else "🎭 场景 ✓"
        if st.button(btn_scenes_label, use_container_width=True):
            state.switch_section("scenes")

        btn_acts_label = "🎬 场次" if current_section != "acts" else "🎬 场次 ✓"
        if st.button(btn_acts_label, use_container_width=True):
            state.switch_section("acts")

        btn_export_label = "📋 剧本导出" if current_section != "export" else "📋 剧本导出 ✓"
        if st.button(btn_export_label, use_container_width=True):
            state.switch_section("export")

    # 右侧主内容区
    current_section = st.session_state.get("current_section", "original")

    if current_section == "original":
        original.render(project)
    elif current_section == "characters":
        characters.render(project)
    elif current_section == "scenes":
        scenes.render(project)
    elif current_section == "acts":
        acts.render(project)
    elif current_section == "export":
        export.render(project)
    else:
        st.error("未知页面，请重新选择导航项。")

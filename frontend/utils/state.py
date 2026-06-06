"""
state.py
负责 Streamlit session_state 的初始化与状态切换封装。
所有页面状态统一在此管理，避免散落在各个视图文件中。
"""

import streamlit as st


def init_session_state():
    """
    初始化 session_state 中的全局状态变量。
    如果已经存在则不会覆盖，保证页面刷新后状态不丢失。
    """
    # 当前正在编辑的项目 id，None 表示在项目首页
    if "current_project_id" not in st.session_state:
        st.session_state.current_project_id = None

    # 当前编辑页面：original / characters / scenes / plots / screenplay_preview / export / audit_report
    if "current_section" not in st.session_state:
        st.session_state.current_section = "original"

    # 当前选中的情节 id，用于情节编辑
    if "selected_plot_id" not in st.session_state:
        st.session_state.selected_plot_id = None

    # 控制是否显示新建项目表单
    if "show_new_project_form" not in st.session_state:
        st.session_state.show_new_project_form = False

    # 后端联调状态：这些 key 对应 V0+V1 pipeline 的 project/job/artifact 进度。
    # 页面刷新时保留它们，避免后端 job 轮询中断后白屏。
    defaults = {
        "backend_project_id": None,
        "backend_chapters": [],
        "backend_job_id": None,
        "backend_job_status": "idle",
        "backend_current_step": None,
        "backend_error": None,
        "backend_artifacts": [],
        "screenplay_data": {},
        "screenplay_yaml": "",
        "rendered_markdown": "",
        "selected_scene": None,
        "selected_character": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def go_home():
    """
    返回项目首页：清空当前项目 id 和编辑页面状态。
    """
    st.session_state.current_project_id = None
    st.session_state.current_section = "original"
    st.session_state.selected_plot_id = None
    st.session_state.selected_scene = None
    st.session_state.selected_character = None
    st.session_state.show_new_project_form = False
    # 使用 rerun 让页面立即刷新
    st.rerun()


def enter_project(project_id: str):
    """
    进入指定项目的编辑页面，默认显示原文管理。
    """
    st.session_state.current_project_id = project_id
    st.session_state.current_section = "original"
    st.session_state.selected_plot_id = None
    st.session_state.selected_scene = None
    st.session_state.selected_character = None
    st.session_state.show_new_project_form = False
    st.rerun()


def switch_section(section: str):
    """
    切换当前编辑页面（original / characters / scenes / plots / screenplay_preview / export / audit_report）。
    """
    if section in ("original", "characters", "scenes", "plots", "screenplay_preview", "export", "audit_report"):
        st.session_state.current_section = section
        # 切换到非情节页面时，清空 selected_plot_id
        if section != "plots":
            st.session_state.selected_plot_id = None
        st.rerun()


def select_plot(plot_id: str | None):
    """
    选中指定情节，进入情节编辑状态。
    """
    st.session_state.selected_plot_id = plot_id
    st.session_state.current_section = "plots"
    st.rerun()


def toggle_new_project_form(show: bool | None = None):
    """
    切换新建项目表单的显示状态。
    如果不传参数，则取反当前状态。
    """
    if show is None:
        st.session_state.show_new_project_form = not st.session_state.show_new_project_form
    else:
        st.session_state.show_new_project_form = show
    st.rerun()

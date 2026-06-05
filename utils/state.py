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

    # 当前编辑页面：original / characters / scenes / acts
    if "current_section" not in st.session_state:
        st.session_state.current_section = "original"

    # 当前选中的场次 id，用于场次编辑
    if "selected_act_id" not in st.session_state:
        st.session_state.selected_act_id = None

    # 控制是否显示新建项目表单
    if "show_new_project_form" not in st.session_state:
        st.session_state.show_new_project_form = False


def go_home():
    """
    返回项目首页：清空当前项目 id 和编辑页面状态。
    """
    st.session_state.current_project_id = None
    st.session_state.current_section = "original"
    st.session_state.selected_act_id = None
    st.session_state.show_new_project_form = False
    # 使用 rerun 让页面立即刷新
    st.rerun()


def enter_project(project_id: str):
    """
    进入指定项目的编辑页面，默认显示原文管理。
    """
    st.session_state.current_project_id = project_id
    st.session_state.current_section = "original"
    st.session_state.selected_act_id = None
    st.session_state.show_new_project_form = False
    st.rerun()


def switch_section(section: str):
    """
    切换当前编辑页面（original / characters / scenes / acts）。
    """
    if section in ("original", "characters", "scenes", "acts"):
        st.session_state.current_section = section
        # 切换到非场次页面时，清空 selected_act_id
        if section != "acts":
            st.session_state.selected_act_id = None
        st.rerun()


def select_act(act_id: str | None):
    """
    选中指定场次，进入场次编辑状态。
    """
    st.session_state.selected_act_id = act_id
    st.session_state.current_section = "acts"
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

"""
app.py
AI 小说转剧本工具 —— Streamlit 应用入口。

职责：
1. 初始化页面配置（标题、布局等）。
2. 初始化 session_state。
3. 根据 current_project_id 判断显示首页还是编辑页面。
"""

import streamlit as st
from frontend.utils import state, theme
from frontend.views import home, editor


def main():
    # 页面基础配置
    st.set_page_config(
        page_title="AI 小说转剧本工具",
        page_icon="🎬",
        layout="wide",
        initial_sidebar_state="auto",
    )

    # 注入侘寂文艺主题
    theme.inject()

    # 初始化全局状态
    state.init_session_state()

    # 根据 current_project_id 路由到对应页面
    current_project_id = st.session_state.get("current_project_id")

    if current_project_id is None:
        # 项目首页
        home.render()
    else:
        # 项目编辑页面（包含左侧导航和右侧内容）
        editor.render()


if __name__ == "__main__":
    main()

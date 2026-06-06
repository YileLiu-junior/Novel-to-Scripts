"""
home.py
项目首页视图：展示已有项目卡片、空状态提示、新建项目表单。
"""

import streamlit as st
from frontend import api_client
from frontend.utils import storage, state


def render():
    """
    渲染项目首页。
    """
    st.title("AI 小说转剧本工具")
    st.markdown("---")

    # 获取所有项目
    projects = storage.get_all_projects()

    # 顶部操作栏：新建项目按钮
    col1, col2 = st.columns([6, 1])
    with col1:
        st.subheader(f"项目列表（共 {len(projects)} 个）")
    with col2:
        # 垂直居中按钮
        st.write("")
        st.write("")
        if st.button("➕ 新建项目", use_container_width=True):
            state.toggle_new_project_form(True)

    # 新建项目表单
    if st.session_state.get("show_new_project_form", False):
        with st.container(border=True):
            st.markdown("#### 新建项目")
            with st.form("new_project_form", clear_on_submit=True):
                name = st.text_input("项目名称", placeholder="请输入项目名称")
                description = st.text_area("简介", placeholder="请输入项目简介（可选）")
                c1, c2 = st.columns(2)
                with c1:
                    submitted = st.form_submit_button("✅ 创建", use_container_width=True)
                with c2:
                    cancelled = st.form_submit_button("❌ 取消", use_container_width=True)

                if submitted:
                    if not name or not name.strip():
                        st.error("项目名称不能为空")
                    else:
                        new_project = storage.create_project(name.strip(), description.strip())
                        # 创建项目时同步创建后端 project。后端不可用时保留本地项目，
                        # 用户可稍后在原文页重新连接，不让首页流程中断。
                        try:
                            backend_project = api_client.create_project(
                                title=name.strip(),
                                logline=description.strip() or None,
                            )
                            storage.update_project(
                                new_project["id"],
                                {"backend_project_id": backend_project.get("id")},
                            )
                            new_project["backend_project_id"] = backend_project.get("id")
                        except api_client.ApiClientError as exc:
                            st.warning(f"本地项目已创建，但暂未连接后端：{exc.message}")
                        st.success(f"项目「{new_project['name']}」创建成功！")
                        # 自动进入新项目
                        state.enter_project(new_project["id"])

                if cancelled:
                    state.toggle_new_project_form(False)

    st.markdown("---")

    # 空状态提示
    if not projects:
        st.info("暂无项目，请点击右上角 **➕ 新建项目** 按钮创建一个。")
        return

    # 项目卡片展示（每行 3 个）
    cols_per_row = 3
    for i in range(0, len(projects), cols_per_row):
        row_projects = projects[i : i + cols_per_row]
        cols = st.columns(cols_per_row)
        for idx, project in enumerate(row_projects):
            with cols[idx]:
                with st.container(border=True):
                    st.markdown(f"**{project.get('name', '未命名项目')}**")
                    desc = project.get("description", "")
                    # 简介最多显示两行
                    if desc:
                        display_desc = desc if len(desc) <= 60 else desc[:60] + "..."
                        st.caption(display_desc)
                    else:
                        st.caption("暂无简介")

                    created = project.get("created_at", "")[:10]
                    st.caption(f"🕒 创建时间：{created}")

                    # 操作按钮
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("进入项目", key=f"open_project_{project['id']}", use_container_width=True):
                            state.enter_project(project["id"])
                    with c2:
                        # 删除项目按钮
                        confirm_key = f"confirm_delete_{project['id']}"
                        if confirm_key not in st.session_state:
                            st.session_state[confirm_key] = False

                        if not st.session_state.get(confirm_key, False):
                            if st.button("🗑️ 删除", key=f"del_btn_{project['id']}", use_container_width=True):
                                st.session_state[confirm_key] = True
                                st.rerun()
                        else:
                            st.warning("确定要删除该项目吗？此操作不可恢复。")
                            c3, c4 = st.columns(2)
                            with c3:
                                if st.button("确认删除", key=f"confirm_del_{project['id']}", use_container_width=True):
                                    # 执行删除
                                    deleted = storage.delete_project(project["id"])
                                    if deleted:
                                        # 如果删除的是当前正在编辑的项目，清空状态
                                        if st.session_state.get("current_project_id") == project["id"]:
                                            st.session_state.current_project_id = None
                                            st.session_state.current_section = "original"
                                            st.session_state.selected_act_id = None
                                        st.session_state[confirm_key] = False
                                        st.success("项目已删除。")
                                        st.rerun()
                            with c4:
                                if st.button("取消", key=f"cancel_del_{project['id']}", use_container_width=True):
                                    st.session_state[confirm_key] = False
                                    st.rerun()

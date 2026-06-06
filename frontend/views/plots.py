# -*- coding: utf-8 -*-
"""
plots.py
情节页面：展示后端 frontend_data 中的情节数据及因果关系。
数据来源为 api_client.get_frontend_data()，保存通过 api_client.save_frontend_data()。
支持情节的查看、添加、编辑、删除功能。
"""

from __future__ import annotations

import streamlit as st

from frontend import api_client, backend_types as bt


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------

def _next_event_id(events_list: list) -> str:
    """生成下一个事件 ID，格式为 event_XXX（三位数字，从 001 开始）。"""
    max_num = 0
    for e in events_list:
        eid = e.get("id", "")
        if eid.startswith("event_"):
            try:
                num = int(eid.split("_")[1])
                if num > max_num:
                    max_num = num
            except (ValueError, IndexError):
                pass
    return f"event_{max_num + 1:03d}"


def _check_event_title_unique(title: str, current_id: str, events_list: list) -> bool:
    """校验事件标题在列表中是否唯一（排除自身）。返回 True 表示唯一。"""
    for e in events_list:
        if e.get("id") != current_id and e.get("title", "").strip().lower() == title.strip().lower():
            return False
    return True


def _save_to_backend(project: dict, plots: list, causal_relations: list) -> bool:
    """保存情节和因果关系数据到后端 frontend_data。"""
    backend_pid = project.get("backend_project_id")
    if not backend_pid:
        st.error("无法保存：缺少后端项目 ID")
        return False
    try:
        with st.spinner("保存中..."):
            result = api_client.save_frontend_data(backend_pid, {
                "characters": st.session_state.get("_fd_characters", []),
                "character_relations": st.session_state.get("_fd_char_relations", []),
                "scenes": st.session_state.get("_fd_scenes", []),
                "scene_relations": st.session_state.get("_fd_scene_relations", []),
                "plots": plots,
                "causal_relations": causal_relations,
            })
            # 更新 session_state 缓存
            st.session_state["_fd_plots"] = result.get("plots", plots)
            st.session_state["_fd_causal_relations"] = result.get("causal_relations", causal_relations)
            st.success("保存成功")
            return True
    except api_client.ApiClientError as exc:
        st.error(f"保存失败：{exc.message}")
        return False


def _load_fd(project: dict) -> dict | None:
    """初始化并获取 frontend_data，结果缓存到 session_state。"""
    backend_pid = project.get("backend_project_id")
    if not backend_pid:
        return None
    try:
        fd = api_client.init_frontend_data(backend_pid)
    except api_client.ApiClientError:
        return None
    # 缓存各模块数据到 session_state
    st.session_state["_fd_characters"] = fd.get("characters", [])
    st.session_state["_fd_char_relations"] = fd.get("character_relations", [])
    st.session_state["_fd_scenes"] = fd.get("scenes", [])
    st.session_state["_fd_scene_relations"] = fd.get("scene_relations", [])
    st.session_state["_fd_plots"] = fd.get("plots", [])
    st.session_state["_fd_causal_relations"] = fd.get("causal_relations", [])
    return fd


# ---------------------------------------------------------------------------
# 情节展示（非编辑状态）
# ---------------------------------------------------------------------------

def _render_event_item(event: dict, char_map: dict[str, str], project: dict,
                       plots_list: list, causal_relations: list) -> None:
    """渲染单条事件/情节（非编辑状态）。"""
    event_id = event.get("id", "")
    title = event.get("title") or "未命名事件"
    description = event.get("summary") or event.get("description") or "暂无描述"

    # 描述截断 80 字
    if len(description) > 80:
        description = description[:80] + "..."

    # 涉及角色（映射为名称）
    character_ids = bt.as_list(event.get("characters", []))
    character_names = [char_map.get(cid, cid) for cid in character_ids if cid]
    characters_str = "、".join(character_names) if character_names else "暂无关联角色"

    # 类型/重要程度
    event_type = event.get("type", "")
    importance = event.get("importance", "")

    with st.container(border=True):
        # 标题
        st.markdown(f"**{title}**")

        # 事件 ID
        st.caption(f"ID: {event_id}")

        # 类型 / 重要程度
        type_parts = []
        if event_type:
            type_parts.append(f"类型：{event_type}")
        if importance:
            type_parts.append(f"重要程度：{importance}")
        if type_parts:
            st.caption(" | ".join(type_parts))

        # 描述（截断显示）
        st.write(description)

        # 关联角色（摘要）
        st.write(f"关联角色：{characters_str}")

        # 操作按钮：编辑 + 删除
        c1, c2 = st.columns(2)

        with c1:
            if st.button("编辑", key=f"plot_edit_{event_id}", use_container_width=True):
                st.session_state["editing_plot_id"] = event_id
                st.rerun()

        with c2:
            confirm_key = f"plot_delete_confirm_{event_id}"
            if st.session_state.get(confirm_key):
                if st.button(
                    "确认删除",
                    key=f"plot_delete_yes_{event_id}",
                    type="primary",
                    use_container_width=True,
                ):
                    updated_plots = [e for e in plots_list if e.get("id") != event_id]
                    if _save_to_backend(project, updated_plots, causal_relations):
                        st.session_state.pop(confirm_key, None)
                        if st.session_state.get("editing_plot_id") == event_id:
                            st.session_state.pop("editing_plot_id", None)
                        st.success(f"情节「{title}」已删除。")
                        st.rerun()
                if st.button(
                    "取消",
                    key=f"plot_delete_no_{event_id}",
                    use_container_width=True,
                ):
                    st.session_state.pop(confirm_key, None)
                    st.rerun()
            else:
                if st.button(
                    "删除",
                    key=f"plot_delete_{event_id}",
                    use_container_width=True,
                ):
                    st.session_state[confirm_key] = True
                    st.rerun()


# ---------------------------------------------------------------------------
# 情节编辑表单
# ---------------------------------------------------------------------------

def _render_event_editor(event: dict, char_map: dict[str, str], project: dict,
                         plots_list: list, causal_relations: list) -> None:
    """渲染情节编辑表单。"""
    event_id = event.get("id", "")
    title = event.get("title", "")
    summary = event.get("summary") or event.get("description") or ""
    event_type = event.get("type", "")
    importance = event.get("importance", "")

    # 涉及角色（转为逗号分隔字符串用于编辑）
    character_ids = bt.as_list(event.get("characters", []))
    character_names = [char_map.get(cid, cid) for cid in character_ids if cid]
    characters_str = "，".join(character_names) if character_names else ""

    with st.container(border=True):
        st.markdown(f"#### 编辑情节（ID: {event_id}）")
        st.caption("ID 不可编辑")

        with st.form(f"edit_plot_form_{event_id}"):
            title_val = st.text_input("事件标题", value=title)
            description_val = st.text_area("事件描述", value=summary, height=150)
            characters_val = st.text_input("关联角色（逗号分隔）", value=characters_str)
            event_type_val = st.text_input("事件类型", value=event_type)
            importance_val = st.text_input("重要程度", value=importance)

            c1, c2 = st.columns(2)
            with c1:
                submitted = st.form_submit_button("保存", use_container_width=True)
            with c2:
                cancelled = st.form_submit_button("取消", use_container_width=True)

            if submitted:
                if not title_val or not title_val.strip():
                    st.error("事件标题不能为空")
                    return

                if not _check_event_title_unique(title_val.strip(), event_id, plots_list):
                    st.error(f"事件标题「{title_val.strip()}」已存在，请使用其他标题。")
                    return

                # 解析角色：从逗号分隔字符串转回 ID 列表
                # 构建 name→id 反向映射
                name_to_id = {v: k for k, v in char_map.items()}
                new_character_ids = []
                for name_part in characters_val.split("，"):
                    name_part = name_part.strip()
                    if not name_part:
                        continue
                    # 先尝试精确匹配名称，找不到则保留原始值
                    if name_part in name_to_id:
                        new_character_ids.append(name_to_id[name_part])
                    else:
                        # 尝试模糊匹配
                        for cid, cname in char_map.items():
                            if cname == name_part:
                                new_character_ids.append(cid)
                                break
                        else:
                            new_character_ids.append(name_part)

                # 更新事件字段
                updated_plots = []
                for e in plots_list:
                    if e.get("id") == event_id:
                        updated_event = dict(e)
                        updated_event["title"] = title_val.strip()
                        updated_event["description"] = description_val.strip()
                        updated_event["summary"] = description_val.strip()
                        updated_event["characters"] = new_character_ids
                        updated_event["type"] = event_type_val.strip()
                        updated_event["importance"] = importance_val.strip()
                        updated_plots.append(updated_event)
                    else:
                        updated_plots.append(e)

                if _save_to_backend(project, updated_plots, causal_relations):
                    st.session_state.pop("editing_plot_id", None)
                    st.success(f"情节「{title_val.strip()}」保存成功！")
                    st.rerun()

            if cancelled:
                st.session_state.pop("editing_plot_id", None)
                st.rerun()


# ---------------------------------------------------------------------------
# 添加情节
# ---------------------------------------------------------------------------

def _render_add_event(project: dict, char_map: dict[str, str],
                      plots_list: list, causal_relations: list) -> None:
    """渲染添加情节的表单区域。"""
    backend_pid = project.get("backend_project_id", "")

    show_form_key = f"show_add_event_form_{backend_pid}"
    if show_form_key not in st.session_state:
        st.session_state[show_form_key] = False

    if not st.session_state.get(show_form_key, False):
        if st.button("添加情节", key=f"btn_add_event_{backend_pid}", use_container_width=True):
            st.session_state[show_form_key] = True
            st.rerun()
    else:
        with st.container(border=True):
            st.markdown("#### 添加新情节")
            with st.form(f"add_event_form_{backend_pid}", clear_on_submit=True):
                title = st.text_input("事件标题", placeholder="例如：主角发现真相")
                description = st.text_area("事件描述", placeholder="请输入该情节的详细描述...", height=150)
                characters = st.text_input("关联角色（逗号分隔）", placeholder="例如：张三，李四")
                event_type = st.text_input("事件类型", placeholder="例如：转折、高潮、铺垫")
                importance = st.text_input("重要程度", placeholder="例如：高、中、低")

                c1, c2 = st.columns(2)
                with c1:
                    submitted = st.form_submit_button("添加", use_container_width=True)
                with c2:
                    cancelled = st.form_submit_button("取消", use_container_width=True)

                if submitted:
                    if not title or not title.strip():
                        st.error("事件标题不能为空")
                    else:
                        if not _check_event_title_unique(title.strip(), "", plots_list):
                            st.error(f"事件标题「{title.strip()}」已存在，请使用其他标题。")
                        else:
                            # 解析角色：从逗号分隔字符串转回 ID 列表
                            name_to_id = {v: k for k, v in char_map.items()}
                            new_character_ids = []
                            if characters:
                                for name_part in characters.split("，"):
                                    name_part = name_part.strip()
                                    if not name_part:
                                        continue
                                    if name_part in name_to_id:
                                        new_character_ids.append(name_to_id[name_part])
                                    else:
                                        for cid, cname in char_map.items():
                                            if cname == name_part:
                                                new_character_ids.append(cid)
                                                break
                                        else:
                                            new_character_ids.append(name_part)

                            new_event = {
                                "id": _next_event_id(plots_list),
                                "title": title.strip(),
                                "summary": description.strip(),
                                "description": description.strip(),
                                "characters": new_character_ids,
                                "type": event_type.strip(),
                                "importance": importance.strip(),
                                "source_refs": [],
                            }
                            updated_plots = plots_list + [new_event]
                            if _save_to_backend(project, updated_plots, causal_relations):
                                st.success(f"情节「{new_event['title']}」添加成功！")
                                st.session_state[show_form_key] = False
                                st.rerun()

                if cancelled:
                    st.session_state[show_form_key] = False
                    st.rerun()


# ---------------------------------------------------------------------------
# 因果关系
# ---------------------------------------------------------------------------

def _render_causal_relations(plots_list: list, causal_relations: list) -> None:
    """渲染因果关系区域。实时从 plots 构建 ID→title 映射。"""
    st.markdown("---")
    st.subheader("因果关系")

    # 从当前 plots_list 实时构建映射
    evt_map = {e.get("id", ""): e.get("title", e.get("id", "")) for e in plots_list if e.get("id")}

    edges = bt.as_list(causal_relations)

    if not edges:
        st.info("暂无因果关系数据")
        return

    rows = []
    for edge in edges:
        from_id = edge.get("from", "")
        to_id = edge.get("to", "")
        from_title = evt_map.get(from_id, from_id) if from_id else "未知"
        to_title = evt_map.get(to_id, to_id) if to_id else "未知"
        relation = edge.get("relation", "")
        description = edge.get("description", "")
        rows.append({
            "from": from_title,
            "relation": relation,
            "to": to_title,
            "description": description,
        })

    st.dataframe(
        rows,
        column_order=["from", "relation", "to", "description"],
        column_config={
            "from": st.column_config.TextColumn("起因事件"),
            "relation": st.column_config.TextColumn("关系"),
            "to": st.column_config.TextColumn("结果事件"),
            "description": st.column_config.TextColumn("描述"),
        },
        use_container_width=True,
        hide_index=True,
    )


# ---------------------------------------------------------------------------
# 主入口
# ---------------------------------------------------------------------------

def render(project: dict) -> None:
    """渲染情节页面（事件列表 + 因果关系）。数据来源为 frontend_data API。"""
    st.header("📖 情节")

    # 获取后端项目 ID
    backend_pid = project.get("backend_project_id")
    if not backend_pid:
        st.info("暂无后端项目关联，请先创建项目并导入原文。")
        return

    # 初始化 + 获取 frontend_data
    fd = _load_fd(project)
    if fd is None:
        st.warning("正在初始化可编辑数据...")
        return

    plots = st.session_state.get("_fd_plots", fd.get("plots", []))
    causal_relations = st.session_state.get("_fd_causal_relations", fd.get("causal_relations", []))

    # 构建角色 ID -> 名称映射（从缓存的人物数据）
    characters = st.session_state.get("_fd_characters", [])
    char_map = {c.get("id", ""): c.get("name", c.get("id", "")) for c in characters if c.get("id")}

    # 空状态
    if not plots:
        st.info("暂无情节数据。请先生成结构化剧本，或手动添加情节。")

    # 获取当前编辑状态
    editing_id = st.session_state.get("editing_plot_id")

    # 逐条展示：编辑中的显示编辑表单，其余显示普通卡片
    for event in plots:
        if event.get("id") == editing_id:
            _render_event_editor(event, char_map, project, plots, causal_relations)
        else:
            _render_event_item(event, char_map, project, plots, causal_relations)

    # 添加情节按钮 + 表单
    _render_add_event(project, char_map, plots, causal_relations)

    # 因果关系
    _render_causal_relations(plots, causal_relations)

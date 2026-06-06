# -*- coding: utf-8 -*-
"""
scenes.py
场景管理页面：展示后端 frontend_data 中的场景数据及场景关系。
数据来源为 api_client.get_frontend_data()，保存通过 api_client.save_frontend_data()。
支持场景的查看、编辑、删除功能。

frontend_data 中场景使用扁平结构：
  id, title, sequence, location, time, interior_exterior, heading_text,
  characters, dramatic_purpose, related_events, action, dialogue, source_refs
"""

from __future__ import annotations

import streamlit as st

from frontend import api_client, backend_types as bt


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------

def _next_scene_id(scenes_list: list) -> str:
    """生成下一个场景 ID，格式为 scene_XXX（三位数字，从 001 开始）。"""
    max_num = 0
    for s in scenes_list:
        sid = s.get("id", "")
        if sid.startswith("scene_"):
            try:
                num = int(sid.split("_")[1])
                if num > max_num:
                    max_num = num
            except (ValueError, IndexError):
                pass
    return f"scene_{max_num + 1:03d}"


def _check_scene_title_unique(title: str, current_id: str, scenes_list: list) -> bool:
    """检查场景标题是否唯一（排除当前正在编辑的场景自身）。"""
    for s in scenes_list:
        if s.get("id") != current_id and s.get("title", "").strip().lower() == title.strip().lower():
            return False
    return True


def _parse_multiline_to_list(text: str) -> list:
    """将多行文本按逗号或换行分割为列表，自动去除空白和空项。"""
    if not text or not text.strip():
        return []
    parts = []
    for line in text.strip().splitlines():
        for segment in line.split(","):
            segment = segment.strip()
            if segment:
                parts.append(segment)
    return parts


def _list_to_multiline(items: list) -> str:
    """将列表转为多行文本，每项一行。"""
    return "\n".join(str(item) for item in bt.as_list(items))


def _get_ie_index(current_value: str | None) -> int:
    """根据 interior_exterior 当前值返回 selectbox 的 index。"""
    options = ["未设置", "内景", "外景", "内外景"]
    if current_value:
        for i, opt in enumerate(options):
            if opt == current_value:
                return i
    return 0


def _save_to_backend(project: dict, scenes: list, scene_relations: list) -> bool:
    """保存场景和关系数据到后端 frontend_data。"""
    backend_pid = project.get("backend_project_id")
    if not backend_pid:
        st.error("无法保存：缺少后端项目 ID")
        return False
    try:
        with st.spinner("保存中..."):
            result = api_client.save_frontend_data(backend_pid, {
                "characters": st.session_state.get("_fd_characters", []),
                "character_relations": st.session_state.get("_fd_char_relations", []),
                "scenes": scenes,
                "scene_relations": scene_relations,
                "plots": st.session_state.get("_fd_plots", []),
                "causal_relations": st.session_state.get("_fd_causal_relations", []),
            })
            # 更新 session_state 缓存
            st.session_state["_fd_scenes"] = result.get("scenes", scenes)
            st.session_state["_fd_scene_relations"] = result.get("scene_relations", scene_relations)
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
# 场景卡片（非编辑状态）
# ---------------------------------------------------------------------------

def _render_scene_card(scene: dict, project: dict, scenes_list: list, scene_relations: list) -> None:
    """渲染单个场景卡片（查看模式），包含编辑和删除按钮。"""
    # frontend_data 扁平结构
    sequence = scene.get("sequence", "")
    title = scene.get("title", "未命名场景")
    location = scene.get("location", "未设置")
    time = scene.get("time", "未设置")
    ie = scene.get("interior_exterior", "未设置")
    heading_text = scene.get("heading_text", "无")

    with st.container(border=True):
        # 序号 + 标题
        if sequence:
            st.markdown(f"**{sequence}. {title}**")
        else:
            st.markdown(f"**{title}**")

        # 场景标题文本
        st.caption(f"场景标题文本：{heading_text}")

        # 地点 / 时间 / 内外景
        st.caption(f"地点：{location} | 时间：{time} | 内外景：{ie}")

        # 戏剧目的（截断 50 字）
        purposes = bt.as_list(scene.get("dramatic_purpose"))
        purposes_str = "；".join(str(p) for p in purposes) if purposes else "暂无"
        if len(purposes_str) > 50:
            purposes_str = purposes_str[:50] + "..."
        st.write(f"戏剧目的：{purposes_str}")

        # 操作按钮：编辑 + 删除
        c1, c2 = st.columns(2)
        scene_id = scene.get("id", "")

        with c1:
            if st.button("编辑", key=f"scene_edit_{scene_id}", use_container_width=True):
                st.session_state["editing_scene_id"] = scene_id
                st.rerun()

        with c2:
            confirm_key = f"scene_delete_confirm_{scene_id}"
            if st.session_state.get(confirm_key):
                if st.button(
                    "确认删除",
                    key=f"scene_delete_yes_{scene_id}",
                    type="primary",
                    use_container_width=True,
                ):
                    updated_scenes = [s for s in scenes_list if s.get("id") != scene_id]
                    if _save_to_backend(project, updated_scenes, scene_relations):
                        st.session_state.pop(confirm_key, None)
                        if st.session_state.get("editing_scene_id") == scene_id:
                            st.session_state.pop("editing_scene_id", None)
                        st.success(f"场景「{title}」已删除。")
                        st.rerun()
                if st.button(
                    "取消",
                    key=f"scene_delete_no_{scene_id}",
                    use_container_width=True,
                ):
                    st.session_state.pop(confirm_key, None)
                    st.rerun()
            else:
                if st.button(
                    "删除",
                    key=f"scene_delete_{scene_id}",
                    use_container_width=True,
                ):
                    st.session_state[confirm_key] = True
                    st.rerun()

        # 展开查看详细信息
        with st.expander("展开查看 action / dialogue / source_refs", expanded=False):
            st.markdown("**Action**")
            for action in bt.as_list(scene.get("action")):
                st.write(action)
            st.markdown("**Dialogue**")
            st.json(scene.get("dialogue", []))
            st.markdown("**Source Refs**")
            st.json(scene.get("source_refs", []))


# ---------------------------------------------------------------------------
# 场景编辑表单
# ---------------------------------------------------------------------------

def _render_scene_editor(scene: dict, project: dict, scenes_list: list, scene_relations: list) -> None:
    """渲染场景编辑表单。使用 frontend_data 扁平字段。"""
    scene_id = scene.get("id", "")

    with st.container(border=True):
        st.markdown(f"#### 编辑场景（ID: {scene_id}）")
        st.caption("ID 不可编辑")

        with st.form(f"edit_scene_form_{scene_id}"):
            # 标题
            title = st.text_input("场景标题", value=scene.get("title", ""))

            # 序号
            sequence = st.text_input("序号", value=str(scene.get("sequence", "")))

            # 场景标题文本
            heading_text = st.text_input("场景标题文本", value=scene.get("heading_text", ""))

            # 地点
            location = st.text_input("地点", value=scene.get("location", ""))

            # 时间
            time = st.text_input("时间", value=scene.get("time", ""))

            # 内景/外景
            current_ie = scene.get("interior_exterior", "未设置")
            interior_exterior = st.selectbox(
                "内景/外景",
                ["未设置", "内景", "外景", "内外景"],
                index=_get_ie_index(current_ie),
            )

            # 戏剧目的（多行文本，保存转列表）
            purposes_str = _list_to_multiline(scene.get("dramatic_purpose", []))
            dramatic_purpose = st.text_area("戏剧目的（逗号或换行分隔）", value=purposes_str)

            # Action（多行文本，保存转列表）
            action_str = _list_to_multiline(scene.get("action", []))
            action = st.text_area("Action（逗号或换行分隔）", value=action_str, height=120)

            # 提交按钮
            c1, c2 = st.columns(2)
            with c1:
                submitted = st.form_submit_button("保存", use_container_width=True)
            with c2:
                cancelled = st.form_submit_button("取消", use_container_width=True)

            if submitted:
                if not title or not title.strip():
                    st.error("场景标题不能为空")
                elif not _check_scene_title_unique(title.strip(), scene_id, scenes_list):
                    st.error(f"场景标题「{title.strip()}」已存在，请使用其他标题")
                else:
                    updated_scene = dict(scene)
                    updated_scene["title"] = title.strip()

                    # 扁平字段直接更新
                    try:
                        updated_scene["sequence"] = int(sequence) if sequence.strip() else 0
                    except ValueError:
                        updated_scene["sequence"] = scene.get("sequence", 0)
                    updated_scene["heading_text"] = heading_text.strip()
                    updated_scene["location"] = location.strip()
                    updated_scene["time"] = time.strip()
                    updated_scene["interior_exterior"] = interior_exterior

                    # 更新 dramatic_purpose（文本 -> 列表）
                    updated_scene["dramatic_purpose"] = _parse_multiline_to_list(dramatic_purpose)

                    # 更新 action（文本 -> 列表）
                    updated_scene["action"] = _parse_multiline_to_list(action)

                    # 替换 scenes_list 中对应的场景
                    updated_scenes = []
                    for s in scenes_list:
                        if s.get("id") == scene_id:
                            updated_scenes.append(updated_scene)
                        else:
                            updated_scenes.append(s)

                    if _save_to_backend(project, updated_scenes, scene_relations):
                        st.session_state.pop("editing_scene_id", None)
                        st.success(f"场景「{title.strip()}」保存成功！")
                        st.rerun()

            if cancelled:
                st.session_state.pop("editing_scene_id", None)
                st.rerun()


# ---------------------------------------------------------------------------
# 添加场景
# ---------------------------------------------------------------------------

def _render_add_scene(project: dict, scenes_list: list, scene_relations: list) -> None:
    """渲染添加场景的表单区域。"""
    backend_pid = project.get("backend_project_id", "")

    show_form_key = f"show_add_scene_form_{backend_pid}"
    if show_form_key not in st.session_state:
        st.session_state[show_form_key] = False

    if not st.session_state.get(show_form_key, False):
        if st.button("添加场景", key=f"btn_add_scene_{backend_pid}", use_container_width=True):
            st.session_state[show_form_key] = True
            st.rerun()
    else:
        with st.container(border=True):
            st.markdown("#### 添加新场景")
            with st.form(f"add_scene_form_{backend_pid}", clear_on_submit=True):
                title = st.text_input("场景标题", placeholder="例如：办公室内景")
                sequence = st.text_input("序号", placeholder="例如：1")
                heading_text = st.text_input("场景标题文本", placeholder="例如：内景/办公室/白天")
                location = st.text_input("地点", placeholder="例如：公司办公室")
                time = st.text_input("时间", placeholder="例如：白天")
                interior_exterior = st.selectbox("内景/外景", ["未设置", "内景", "外景", "内外景"])
                dramatic_purpose = st.text_area("戏剧目的（逗号或换行分隔）", placeholder="请输入该场景的戏剧目的...")
                action = st.text_area("动作描述（逗号或换行分隔）", placeholder="请输入场景内容描述...", height=150)

                c1, c2 = st.columns(2)
                with c1:
                    submitted = st.form_submit_button("添加", use_container_width=True)
                with c2:
                    cancelled = st.form_submit_button("取消", use_container_width=True)

                if submitted:
                    if not title or not title.strip():
                        st.error("场景标题不能为空")
                    elif not _check_scene_title_unique(title.strip(), "", scenes_list):
                        st.error(f"场景标题「{title.strip()}」已存在，请使用其他标题")
                    else:
                        try:
                            seq_num = int(sequence) if sequence.strip() else len(scenes_list) + 1
                        except ValueError:
                            seq_num = len(scenes_list) + 1
                        new_scene = {
                            "id": _next_scene_id(scenes_list),
                            "title": title.strip(),
                            "sequence": seq_num,
                            "heading_text": heading_text.strip() if heading_text else title.strip(),
                            "location": location.strip(),
                            "time": time.strip(),
                            "interior_exterior": interior_exterior,
                            "dramatic_purpose": _parse_multiline_to_list(dramatic_purpose),
                            "action": _parse_multiline_to_list(action),
                            "dialogue": [],
                            "characters": [],
                            "related_events": [],
                            "source_refs": [],
                        }
                        updated_scenes = scenes_list + [new_scene]
                        if _save_to_backend(project, updated_scenes, scene_relations):
                            st.success(f"场景「{new_scene['title']}」添加成功！")
                            st.session_state[show_form_key] = False
                            st.rerun()

                if cancelled:
                    st.session_state[show_form_key] = False
                    st.rerun()


# ---------------------------------------------------------------------------
# 场景关系
# ---------------------------------------------------------------------------

def _render_scene_relations(scenes_list: list, scene_relations: list) -> None:
    """渲染场景关系区域。实时从 scenes 构建 ID→title 映射。"""
    st.markdown("---")
    st.subheader("场景关系")

    if not scene_relations:
        st.info("暂无场景关系数据")
        return

    # 从当前 scenes_list 实时构建映射
    scene_title_map = {s.get("id", ""): s.get("title", "未命名场景") for s in scenes_list}

    rows = []
    for item in bt.as_list(scene_relations):
        from_id = item.get("from", "")
        to_id = item.get("to", "")
        relation = item.get("relation", "")
        description = item.get("description", "")

        from_title = scene_title_map.get(from_id, from_id) if from_id else "未知"
        to_title = scene_title_map.get(to_id, to_id) if to_id else "未知"

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
            "from": st.column_config.TextColumn("场景 A"),
            "relation": st.column_config.TextColumn("关系类型"),
            "to": st.column_config.TextColumn("场景 B"),
            "description": st.column_config.TextColumn("描述"),
        },
        use_container_width=True,
        hide_index=True,
    )


# ---------------------------------------------------------------------------
# 主入口
# ---------------------------------------------------------------------------

def render(project: dict) -> None:
    """渲染场景管理页面。数据来源为 frontend_data API。"""
    st.header("🎬 场景管理")

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

    scenes = st.session_state.get("_fd_scenes", fd.get("scenes", []))
    scene_relations = st.session_state.get("_fd_scene_relations", fd.get("scene_relations", []))

    # 空状态
    if not scenes:
        st.info("暂无场景数据。请先生成结构化剧本，或手动添加场景。")

    # 获取当前编辑状态
    editing_id = st.session_state.get("editing_scene_id")

    # 渲染场景卡片或编辑表单
    for scene in scenes:
        if scene.get("id") == editing_id:
            _render_scene_editor(scene, project, scenes, scene_relations)
        else:
            _render_scene_card(scene, project, scenes, scene_relations)

    # 添加场景按钮 + 表单
    _render_add_scene(project, scenes, scene_relations)

    # 底部场景关系
    _render_scene_relations(scenes, scene_relations)

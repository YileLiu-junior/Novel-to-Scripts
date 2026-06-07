# -*- coding: utf-8 -*-
"""
characters.py
人物管理页面：展示后端 frontend_data 中的人物数据及人物关系。
数据来源为 api_client.get_frontend_data()，保存通过 api_client.save_frontend_data()。
支持人物的添加、编辑、删除功能。

卡片式布局：使用 Streamlit columns 实现网格排列。
"""

from __future__ import annotations

import streamlit as st

from frontend import api_client, backend_types as bt


# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------

_CARDS_PER_ROW = 4  # 每行显示 4 张卡片


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------

def _next_char_id(characters_list: list) -> str:
    """生成下一个人物 ID，格式为 char_XXX（三位数字，从 001 开始）。"""
    max_num = 0
    for c in characters_list:
        cid = c.get("id", "")
        if cid.startswith("char_"):
            try:
                num = int(cid.split("_")[1])
                if num > max_num:
                    max_num = num
            except (ValueError, IndexError):
                pass
    return f"char_{max_num + 1:03d}"


def _check_name_unique(name: str, current_id: str, characters_list: list) -> bool:
    """检查人物姓名是否唯一（排除自身）。返回 True 表示不重复。"""
    for c in characters_list:
        if c.get("id") != current_id and c.get("name", "").strip().lower() == name.strip().lower():
            return False
    return True


def _save_to_backend(project: dict, characters: list, char_relations: list) -> bool:
    """保存人物和关系数据到后端 frontend_data。"""
    backend_pid = project.get("backend_project_id")
    if not backend_pid:
        st.error("无法保存：缺少后端项目 ID")
        return False
    try:
        with st.spinner("保存中..."):
            result = api_client.save_frontend_data(backend_pid, {
                "characters": characters,
                "character_relations": char_relations,
                "scenes": st.session_state.get("_fd_scenes", []),
                "scene_relations": st.session_state.get("_fd_scene_relations", []),
                "plots": st.session_state.get("_fd_plots", []),
                "causal_relations": st.session_state.get("_fd_causal_relations", []),
            })
            # 更新 session_state 缓存
            st.session_state["_fd_characters"] = result.get("characters", characters)
            st.session_state["_fd_char_relations"] = result.get("character_relations", char_relations)
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
# 单张人物卡片（非编辑状态）
# ---------------------------------------------------------------------------

def _render_single_character_card(char: dict, project: dict, characters_list: list, char_relations: list):
    """在单个 column 中渲染一张人物卡片。"""
    name = char.get("name") or "未命名"
    char_id = char.get("id", "")
    role_like_values = {"protagonist", "antagonist", "supporting", "narrative_role", "role"}
    if str(name).strip().lower() in role_like_values:
        name = "未命名人物"

    # 简介截断 40 字（卡片正文显示）
    description = char.get("description", "")
    if description and len(description) > 40:
        description = description[:40] + "..."

    # 卡片容器
    with st.container(border=True):
        # 头像区域（居中，大图标）
        st.markdown(
            f"""
            <div style="
                text-align: center;
                padding: 12px 0 4px 0;
            ">
                <div style="
                    width: 72px;
                    height: 72px;
                    border-radius: 50%;
                    background-color: #2a2a2a;
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 36px;
                    color: #666;
                ">👤</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # 人物名称（头像下方，只显示名称）
        st.markdown(
            f"""
            <div style="
                margin-top: 8px;
                font-size: 15px;
                font-weight: 600;
                text-align: center;
                max-width: 100%;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
                color: #111;
            ">{name}</div>
            """,
            unsafe_allow_html=True,
        )

        # 叙事角色（可选，简短）
        # 描述摘要（可选，最多两行）
        # 底部操作按钮
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        # 删除确认状态
        delete_confirm_key = f"delete_confirm_{char_id}"
        if delete_confirm_key not in st.session_state:
            st.session_state[delete_confirm_key] = False

        if st.session_state.get(delete_confirm_key, False):
            c1, c2 = st.columns(2)
            with c1:
                if st.button("确认删除", key=f"confirm_del_{char_id}", use_container_width=True, type="primary"):
                    updated_characters = [c for c in characters_list if c.get("id") != char_id]
                    if _save_to_backend(project, updated_characters, char_relations):
                        st.session_state[delete_confirm_key] = False
                        st.success(f"人物「{name}」已删除")
                        st.rerun()
            with c2:
                if st.button("取消", key=f"cancel_del_{char_id}", use_container_width=True):
                    st.session_state[delete_confirm_key] = False
                    st.rerun()
        else:
            c1, c2 = st.columns(2)
            with c1:
                if st.button("编辑", key=f"edit_char_{char_id}", use_container_width=True):
                    st.session_state["editing_character_id"] = char_id
                    st.rerun()
            with c2:
                if st.button("删除", key=f"del_char_{char_id}", use_container_width=True):
                    st.session_state[delete_confirm_key] = True
                    st.rerun()


# ---------------------------------------------------------------------------
# 添加人物卡片
# ---------------------------------------------------------------------------

def _render_add_character_card(project: dict, characters_list: list, char_relations: list):
    """渲染添加人物卡片（与人物卡片风格一致）。"""
    backend_pid = project.get("backend_project_id", "")
    show_form_key = f"show_add_form_{backend_pid}"
    if show_form_key not in st.session_state:
        st.session_state[show_form_key] = False

    with st.container(border=True):
        # 添加卡片图标
        st.markdown(
            """
            <div style="
                text-align: center;
                padding: 12px 0 4px 0;
            ">
                <div style="
                    width: 72px;
                    height: 72px;
                    border-radius: 50%;
                    background-color: #2a2a2a;
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 36px;
                    color: #666;
                ">+</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div style="
                margin-top: 4px;
                font-size: 15px;
                font-weight: 600;
                text-align: center;
                max-width: 100%;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
                color: #888;
            ">添加人物</div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        if st.button("点击添加", key=f"btn_add_char_{backend_pid}", use_container_width=True):
            st.session_state[show_form_key] = True
            st.rerun()

    # 添加表单（卡片下方展开）
    if st.session_state.get(show_form_key, False):
        with st.container(border=True):
            st.markdown("#### 添加人物")
            with st.form(f"add_character_form_{backend_pid}", clear_on_submit=True):
                name = st.text_input("人物姓名", placeholder="例如：张三")
                aliases = st.text_input("别名（逗号分隔）", placeholder="例如：小张，老张")
                narrative_role = st.text_input("叙事功能", placeholder="例如：男主角、反派")
                rhythm = st.text_input("语言节奏", placeholder="例如：沉稳、急促")
                diction = st.text_input("措辞风格", placeholder="例如：文雅、粗犷")
                description = st.text_area("人物简介", placeholder="请输入人物背景、性格等简介...")

                c1, c2 = st.columns(2)
                with c1:
                    submitted = st.form_submit_button("添加", use_container_width=True)
                with c2:
                    cancelled = st.form_submit_button("取消", use_container_width=True)

                if submitted:
                    if not name or not name.strip():
                        st.error("人物姓名不能为空")
                    elif not _check_name_unique(name, "", characters_list):
                        st.error(f"人物姓名「{name.strip()}」已存在，请使用其他名称")
                    else:
                        new_aliases = [a.strip() for a in aliases.split("，") if a.strip()] if aliases else []
                        new_character = {
                            "id": _next_char_id(characters_list),
                            "name": name.strip(),
                            "aliases": new_aliases,
                            "narrative_role": narrative_role.strip(),
                            "voice_profile": {
                                "rhythm": rhythm.strip(),
                                "diction": diction.strip(),
                            },
                            "description": description.strip(),
                        }
                        updated_characters = characters_list + [new_character]
                        if _save_to_backend(project, updated_characters, char_relations):
                            st.success(f"人物「{new_character['name']}」添加成功！")
                            st.session_state[show_form_key] = False
                            st.rerun()

                if cancelled:
                    st.session_state[show_form_key] = False
                    st.rerun()


# ---------------------------------------------------------------------------
# 人物编辑表单（全宽，非卡片内）
# ---------------------------------------------------------------------------

def _render_character_editor(char: dict, project: dict, characters_list: list, char_relations: list):
    """渲染人物编辑表单（编辑状态，全宽显示）。"""
    char_id = char.get("id", "")
    name = char.get("name", "")

    # 别名：从列表转为逗号分隔字符串
    aliases = bt.as_list(char.get("aliases", []))
    aliases_str = "，".join(str(a) for a in aliases if a) if aliases else ""

    narrative_role = char.get("narrative_role", "")

    # 语言风格
    voice = char.get("voice_profile", {}) or {}
    rhythm = voice.get("rhythm", "") if isinstance(voice, dict) else ""
    diction = voice.get("diction", "") if isinstance(voice, dict) else ""

    description = char.get("description", "")

    with st.container(border=True):
        st.markdown(f"#### 编辑人物（ID: {char_id}）")
        st.caption("ID 不可编辑")

        with st.form(f"edit_char_form_{char_id}"):
            edited_name = st.text_input("人物姓名", value=name)
            edited_aliases = st.text_input("别名（逗号分隔）", value=aliases_str)
            edited_role = st.text_input("叙事功能", value=narrative_role)
            edited_rhythm = st.text_input("语言节奏", value=rhythm)
            edited_diction = st.text_input("措辞风格", value=diction)
            edited_description = st.text_area("人物简介", value=description, height=100)

            c1, c2 = st.columns(2)
            with c1:
                submitted = st.form_submit_button("保存", use_container_width=True)
            with c2:
                cancelled = st.form_submit_button("取消", use_container_width=True)

            if submitted:
                if not edited_name or not edited_name.strip():
                    st.error("人物姓名不能为空")
                elif not _check_name_unique(edited_name, char_id, characters_list):
                    st.error(f"人物姓名「{edited_name.strip()}」已存在，请使用其他名称")
                else:
                    updated_characters = []
                    for c in characters_list:
                        if c.get("id") == char_id:
                            new_aliases = [a.strip() for a in edited_aliases.split("，") if a.strip()]
                            updated_char = dict(c)
                            updated_char["name"] = edited_name.strip()
                            updated_char["narrative_role"] = edited_role.strip()
                            updated_char["aliases"] = new_aliases
                            updated_char["voice_profile"] = {
                                "rhythm": edited_rhythm.strip(),
                                "diction": edited_diction.strip(),
                            }
                            updated_char["description"] = edited_description.strip()
                            updated_characters.append(updated_char)
                        else:
                            updated_characters.append(c)

                    if _save_to_backend(project, updated_characters, char_relations):
                        st.session_state["editing_character_id"] = None
                        st.rerun()

            if cancelled:
                st.session_state["editing_character_id"] = None
                st.rerun()


# ---------------------------------------------------------------------------
# 人物关系
# ---------------------------------------------------------------------------

def _render_relationships(characters_list: list, char_relations: list):
    """渲染人物关系区域。实时从 characters 构建 ID→name 映射。"""
    st.markdown("---")
    st.subheader("人物关系")

    # 实时从当前 characters_list 构建映射
    char_map = {c.get("id", ""): c.get("name", c.get("id", "")) for c in characters_list if c.get("id")}

    edges = bt.as_list(char_relations)

    if not edges:
        st.info("暂无人物关系数据")
        return

    rows = []
    for edge in edges:
        from_id = edge.get("from", "")
        to_id = edge.get("to", "")
        from_name = char_map.get(from_id, from_id) if from_id else "未知"
        to_name = char_map.get(to_id, to_id) if to_id else "未知"
        relation = edge.get("relation", "")
        current_state = edge.get("current_state", "")
        description = edge.get("description", "")
        rows.append({
            "from": from_name,
            "to": to_name,
            "relation": relation,
            "current_state": current_state,
            "description": description,
        })

    st.dataframe(
        rows,
        column_order=["from", "to", "relation", "current_state", "description"],
        column_config={
            "from": st.column_config.TextColumn("角色 A"),
            "to": st.column_config.TextColumn("角色 B"),
            "relation": st.column_config.TextColumn("关系类型"),
            "current_state": st.column_config.TextColumn("当前状态"),
            "description": st.column_config.TextColumn("描述"),
        },
        use_container_width=True,
        hide_index=True,
    )


# ---------------------------------------------------------------------------
# 主入口
# ---------------------------------------------------------------------------

def render(project: dict):
    """渲染人物管理页面。数据来源为 frontend_data API。"""
    st.header("👤 人物管理")

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

    # fd 结构：{"characters": [...], "character_relations": [...], ...}
    characters = st.session_state.get("_fd_characters", fd.get("characters", []))
    char_relations = st.session_state.get("_fd_char_relations", fd.get("character_relations", []))

    # 空状态提示
    if not characters:
        st.info("暂无人物数据。请先生成结构化剧本，或手动添加人物。")

    # 编辑状态
    editing_id = st.session_state.get("editing_character_id")

    # 如果有正在编辑的人物，全宽显示编辑表单
    if editing_id:
        for char in characters:
            if char.get("id") == editing_id:
                _render_character_editor(char, project, characters, char_relations)
                break

    # 卡片网格布局：计算需要显示为卡片的角色（排除正在编辑的）
    card_chars = [c for c in characters if c.get("id") != editing_id]

    # 按 _CARDS_PER_ROW 分组渲染
    for i in range(0, len(card_chars), _CARDS_PER_ROW):
        row_chars = card_chars[i:i + _CARDS_PER_ROW]
        cols = st.columns(_CARDS_PER_ROW)
        for idx, char in enumerate(row_chars):
            with cols[idx]:
                _render_single_character_card(char, project, characters, char_relations)

    # 添加人物卡片（放在网格下方，也占一列宽度）
    st.markdown("---")
    add_cols = st.columns(_CARDS_PER_ROW)
    with add_cols[0]:
        _render_add_character_card(project, characters, char_relations)

    # 人物关系
    _render_relationships(characters, char_relations)

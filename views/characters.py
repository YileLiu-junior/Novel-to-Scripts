"""
characters.py
人物管理页面：竖向卡片式视图，支持添加/删除人物。
"""

import streamlit as st
import uuid
from utils import storage

# 每行卡片数量
CARDS_PER_ROW = 4


def _render_character_card(char: dict, project_id: str, characters_list: list):
    """
    渲染单个人物竖向卡片。
    卡片上半部分显示头像（占高度一半），下半部分显示信息。
    """
    name = char.get("name") or "未命名"
    role = char.get("role") or "未设置身份"
    description = char.get("description", "")
    # 兼容旧数据没有 avatar 字段的情况
    _ = char.get("avatar", "")

    # 简介截断显示
    if description:
        display_desc = description if len(description) <= 60 else description[:60] + "..."
    else:
        display_desc = "暂无简介"

    # 使用 HTML + CSS 构建竖向卡片
    card_html = f"""
    <div style="
        background-color: #1e1e1e;
        border: 1px solid #333;
        border-radius: 12px;
        padding: 0;
        margin-bottom: 12px;
        height: 360px;
        display: flex;
        flex-direction: column;
        align-items: center;
        box-sizing: border-box;
        overflow: hidden;
    ">
        <!-- 头像区域：占卡片高度一半以上 -->
        <div style="
            width: 100%;
            height: 55%;
            background-color: #2a2a2a;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 72px;
            color: #666;
            flex-shrink: 0;
        ">
            👤
        </div>
        <!-- 信息区域 -->
        <div style="
            width: 100%;
            height: 45%;
            padding: 12px 12px 8px 12px;
            display: flex;
            flex-direction: column;
            align-items: center;
            box-sizing: border-box;
        ">
            <div style="
                font-size: 15px;
                font-weight: bold;
                color: #fff;
                margin-bottom: 4px;
                text-align: center;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
                width: 100%;
            ">{name}</div>
            <div style="
                font-size: 11px;
                color: #888;
                margin-bottom: 6px;
                text-align: center;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
                width: 100%;
            ">🎭 {role}</div>
            <div style="
                font-size: 11px;
                color: #aaa;
                text-align: center;
                line-height: 1.4;
                flex-grow: 1;
                overflow: hidden;
                display: -webkit-box;
                -webkit-line-clamp: 2;
                -webkit-box-orient: vertical;
                width: 100%;
            ">{display_desc}</div>
        </div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

    # 底部操作按钮
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🎨 生成形象", key=f"gen_avatar_{char['id']}", use_container_width=True):
            st.info("该功能暂未实现。")
    with c2:
        if st.button("🖼️ 生成剧照", key=f"gen_still_{char['id']}", use_container_width=True):
            st.info("该功能暂未实现。")

    # 删除按钮（单独一行，较小）
    if st.button("🗑️ 删除", key=f"del_char_{char['id']}", use_container_width=True):
        updated_characters = [c for c in characters_list if c["id"] != char["id"]]
        storage.update_project(project_id, {"characters": updated_characters})
        st.success(f"人物「{name}」已删除")
        st.rerun()


def _render_add_card(project_id: str, characters_list: list):
    """
    渲染"添加人物"竖向卡片，点击后展开表单。
    """
    # 使用 HTML 构建带 + 号的竖向卡片
    add_card_html = """
    <div style="
        background-color: #1e1e1e;
        border: 2px dashed #555;
        border-radius: 12px;
        padding: 0;
        margin-bottom: 12px;
        height: 360px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        box-sizing: border-box;
    ">
        <div style="
            font-size: 64px;
            color: #666;
            margin-bottom: 8px;
        ">+</div>
        <div style="
            font-size: 14px;
            color: #888;
        ">添加人物</div>
    </div>
    """
    st.markdown(add_card_html, unsafe_allow_html=True)

    # 点击卡片后显示表单
    show_form_key = f"show_add_form_{project_id}"
    if show_form_key not in st.session_state:
        st.session_state[show_form_key] = False

    if st.button("点击添加", key=f"btn_add_char_{project_id}", use_container_width=True):
        st.session_state[show_form_key] = True
        st.rerun()

    if st.session_state.get(show_form_key, False):
        with st.container(border=True):
            st.markdown("#### 添加人物")
            with st.form(f"add_character_form_{project_id}", clear_on_submit=True):
                name = st.text_input("人物姓名", placeholder="例如：张三")
                role = st.text_input("人物身份 / 角色", placeholder="例如：男主角、反派")
                description = st.text_area("人物简介", placeholder="请输入人物背景、性格等简介...")

                c1, c2 = st.columns(2)
                with c1:
                    submitted = st.form_submit_button("✅ 添加", use_container_width=True)
                with c2:
                    cancelled = st.form_submit_button("❌ 取消", use_container_width=True)

                if submitted:
                    if not name or not name.strip():
                        st.error("人物姓名不能为空")
                    else:
                        new_character = {
                            "id": str(uuid.uuid4()),
                            "name": name.strip(),
                            "role": role.strip(),
                            "description": description.strip(),
                            "avatar": "",
                        }
                        updated_characters = characters_list + [new_character]
                        storage.update_project(project_id, {"characters": updated_characters})
                        st.success(f"人物「{new_character['name']}」添加成功！")
                        st.session_state[show_form_key] = False
                        st.rerun()

                if cancelled:
                    st.session_state[show_form_key] = False
                    st.rerun()


def render(project: dict):
    """
    渲染人物管理页面（竖向卡片式视图）。
    :param project: 当前项目字典
    """
    st.header("👤 人物管理")
    st.caption("管理剧本中出现的人物角色。")
    st.markdown("---")

    project_id = project.get("id")
    characters_list = project.get("characters", [])

    # 空状态提示
    if not characters_list:
        st.info('暂无人物，请点击下方 **"+ 添加人物"** 创建。')

    # 卡片布局：每行 CARDS_PER_ROW 个
    total_items = len(characters_list) + 1  # +1 是添加卡片

    for row_start in range(0, total_items, CARDS_PER_ROW):
        cols = st.columns(CARDS_PER_ROW)
        for col_idx in range(CARDS_PER_ROW):
            item_idx = row_start + col_idx
            with cols[col_idx]:
                if item_idx < len(characters_list):
                    # 渲染人物卡片
                    _render_character_card(characters_list[item_idx], project_id, characters_list)
                elif item_idx == len(characters_list):
                    # 渲染添加人物卡片
                    _render_add_card(project_id, characters_list)
                else:
                    # 空白占位
                    st.empty()

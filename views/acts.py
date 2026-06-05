"""
acts.py
场次管理页面：管理具体剧情单元，可关联场景背景和出场人物。
支持卡片视图和编辑表单。
"""

import streamlit as st
import uuid
from utils import storage, state

# 每行卡片数量
CARDS_PER_ROW = 3


def _get_scene_name_by_id(project: dict, scene_id: str) -> str:
    """
    根据场景 id 获取场景名称。
    """
    if not scene_id:
        return "未选择场景"
    for scene in project.get("scenes", []):
        if scene.get("id") == scene_id:
            return scene.get("name", "未命名场景")
    return "未选择场景"


def _get_character_names_by_ids(project: dict, character_ids: list) -> list:
    """
    根据人物 id 列表获取人物名称列表。
    兼容旧数据（character_ids 可能为 None）。
    """
    if not character_ids:
        return []
    characters = project.get("characters", [])
    id_to_name = {c["id"]: c.get("name", "未命名") for c in characters}
    return [id_to_name.get(cid, "未知") for cid in character_ids if cid in id_to_name]


def _render_act_card(act: dict, project: dict, acts_list: list):
    """
    渲染单个场次卡片。
    """
    title = act.get("title") or "未命名场次"
    scene_name = _get_scene_name_by_id(project, act.get("scene_id", ""))
    time_str = act.get("time") or "未设置"
    summary = act.get("summary", "")
    # 兼容旧数据：character_ids 可能不存在
    character_ids = act.get("character_ids", []) or []
    character_names = _get_character_names_by_ids(project, character_ids)

    display_summary = summary if len(summary) <= 80 else summary[:80] + "..."
    if not display_summary:
        display_summary = "暂无摘要"

    # 出场人物显示
    if character_names:
        characters_display = "、".join(character_names)
    else:
        characters_display = "暂无出场人物"

    # 使用 HTML + CSS 构建卡片
    card_html = f"""
    <div style="
        background-color: #1e1e1e;
        border: 1px solid #333;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
        height: 280px;
        display: flex;
        flex-direction: column;
        box-sizing: border-box;
    ">
        <div style="
            font-size: 16px;
            font-weight: bold;
            color: #fff;
            margin-bottom: 8px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        ">{title}</div>
        <div style="
            font-size: 12px;
            color: #888;
            margin-bottom: 4px;
        ">🎭 场景：{scene_name}</div>
        <div style="
            font-size: 12px;
            color: #888;
            margin-bottom: 4px;
        ">👤 出场人物：{characters_display}</div>
        <div style="
            font-size: 12px;
            color: #888;
            margin-bottom: 8px;
        ">🕒 时间：{time_str}</div>
        <div style="
            font-size: 12px;
            color: #aaa;
            line-height: 1.4;
            flex-grow: 1;
            overflow: hidden;
            display: -webkit-box;
            -webkit-line-clamp: 3;
            -webkit-box-orient: vertical;
        ">{display_summary}</div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

    # 编辑按钮
    if st.button("✏️ 编辑", key=f"edit_act_{act['id']}", use_container_width=True):
        state.select_act(act["id"])


def _render_add_card(project_id: str, acts_list: list):
    """
    渲染"添加场次"卡片。
    """
    add_card_html = """
    <div style="
        background-color: #1e1e1e;
        border: 2px dashed #555;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
        height: 280px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        box-sizing: border-box;
    ">
        <div style="
            font-size: 48px;
            color: #666;
            margin-bottom: 8px;
        ">+</div>
        <div style="
            font-size: 14px;
            color: #888;
        ">添加场次</div>
    </div>
    """
    st.markdown(add_card_html, unsafe_allow_html=True)

    if st.button("点击添加", key=f"btn_add_act_{project_id}", use_container_width=True):
        new_act = {
            "id": str(uuid.uuid4()),
            "title": f"第 {len(acts_list) + 1} 场",
            "scene_id": "",
            "character_ids": [],
            "time": "",
            "summary": "",
            "content": "",
        }
        updated_acts = acts_list + [new_act]
        storage.update_project(project_id, {"acts": updated_acts})
        state.select_act(new_act["id"])


def _render_act_editor(project: dict):
    """
    渲染场次编辑表单。
    """
    act_id = st.session_state.get("selected_act_id")
    if not act_id:
        return

    acts_list = project.get("acts", [])
    act = None
    for a in acts_list:
        if a.get("id") == act_id:
            act = a
            break

    if not act:
        st.error("场次不存在")
        if st.button("返回场次列表", key="back_from_missing_act"):
            st.session_state.selected_act_id = None
            st.rerun()
        return

    st.subheader(f"✏️ 编辑场次：{act.get('title', '未命名')}")
    st.markdown("---")

    # 构建场景选项
    scenes_list = project.get("scenes", [])
    scene_options = [("", "未选择场景")]
    for scene in scenes_list:
        scene_options.append((scene["id"], scene.get("name", "未命名场景")))

    scene_ids = [s[0] for s in scene_options]
    scene_labels = [s[1] for s in scene_options]

    # 当前选中的场景索引
    current_scene_id = act.get("scene_id", "")
    try:
        current_scene_index = scene_ids.index(current_scene_id)
    except ValueError:
        current_scene_index = 0

    # 构建人物选项（显示文本 -> id 映射）
    characters_list = project.get("characters", [])
    character_options = []
    character_display_to_id = {}
    for char in characters_list:
        display_text = f"{char.get('name', '未命名')}（{char.get('role', '无身份')}）"
        character_options.append(display_text)
        character_display_to_id[display_text] = char["id"]

    # 当前已选中的人物（从 character_ids 映射回显示文本）
    # 兼容旧数据：character_ids 可能不存在或为 None
    current_character_ids = act.get("character_ids", []) or []
    default_selected_displays = []
    for display_text, cid in character_display_to_id.items():
        if cid in current_character_ids:
            default_selected_displays.append(display_text)

    with st.form(f"edit_act_form_{act_id}", clear_on_submit=False):
        title = st.text_input("场次标题", value=act.get("title", ""))
        scene_index = st.selectbox(
            "关联场景",
            range(len(scene_labels)),
            format_func=lambda i: scene_labels[i],
            index=current_scene_index,
        )

        # 出场人物选择
        if character_options:
            selected_character_displays = st.multiselect(
                "出场人物",
                options=character_options,
                default=default_selected_displays,
            )
        else:
            st.info("当前项目暂无人物，请先在“人物”页面添加人物。")
            selected_character_displays = []

        time_str = st.text_input("时间", value=act.get("time", ""), placeholder="例如：夜晚、清晨")
        summary = st.text_area("场次摘要", value=act.get("summary", ""), placeholder="请输入该场次的主要情节摘要...")
        content = st.text_area("场次内容", value=act.get("content", ""), height=200, placeholder="后续用于保存剧本正文...")

        c1, c2 = st.columns(2)
        with c1:
            submitted = st.form_submit_button("💾 保存", use_container_width=True)
        with c2:
            cancelled = st.form_submit_button("❌ 取消", use_container_width=True)

        if submitted:
            selected_scene_id = scene_ids[scene_index]
            selected_character_ids = [
                character_display_to_id[d] for d in selected_character_displays
                if d in character_display_to_id
            ]
            updated_act = {
                "title": title.strip(),
                "scene_id": selected_scene_id,
                "character_ids": selected_character_ids,
                "time": time_str.strip(),
                "summary": summary.strip(),
                "content": content.strip(),
            }
            # 更新 acts 数组
            new_acts = []
            for a in acts_list:
                if a["id"] == act_id:
                    a.update(updated_act)
                new_acts.append(a)
            storage.update_project(project["id"], {"acts": new_acts})
            st.success("场次已保存。")
            # 保存后退出编辑状态，回到卡片列表
            st.session_state.selected_act_id = None
            st.rerun()

        if cancelled:
            # 取消后退出编辑状态，回到卡片列表
            st.session_state.selected_act_id = None
            st.rerun()


def render(project: dict):
    """
    渲染场次管理页面。
    :param project: 当前项目字典
    """
    st.header("🎬 场次管理")
    st.caption("场次指具体剧情单元。每个场次可以关联一个场景背景，并添加多个出场人物。")
    st.markdown("---")

    project_id = project.get("id")
    acts_list = project.get("acts", [])

    # 如果有选中的场次，显示编辑表单
    if st.session_state.get("selected_act_id"):
        _render_act_editor(project)
        return

    # 否则显示卡片列表
    if not acts_list:
        st.info("暂无场次，请点击下方 **+ 添加场次** 创建。")

    # 卡片布局
    total_items = len(acts_list) + 1  # +1 是添加卡片

    for row_start in range(0, total_items, CARDS_PER_ROW):
        cols = st.columns(CARDS_PER_ROW)
        for col_idx in range(CARDS_PER_ROW):
            item_idx = row_start + col_idx
            with cols[col_idx]:
                if item_idx < len(acts_list):
                    _render_act_card(acts_list[item_idx], project, acts_list)
                elif item_idx == len(acts_list):
                    _render_add_card(project_id, acts_list)
                else:
                    st.empty()

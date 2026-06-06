"""
scenes.py
<<<<<<< HEAD
场景管理页面：管理演出背景/地点环境，一个场景可被多个场次重复使用。
"""

import streamlit as st
import uuid
from frontend.utils import storage


def render(project: dict):
    """
    渲染场景管理页面（场景/演出背景管理）。
    :param project: 当前项目字典
    """
    st.header("🎭 场景管理")
    st.caption("场景指演出背景或地点环境，一个场景可以被多个场次重复使用。")
    st.markdown("---")

    project_id = project.get("id")
    scenes_list = project.get("scenes", [])
    acts_list = project.get("acts", [])

    # 添加场景表单
    with st.expander("➕ 添加场景", expanded=False):
        with st.form("add_scene_form", clear_on_submit=True):
            name = st.text_input("场景名称", placeholder="例如：餐厅、皇宫大殿")
            location = st.text_input("地点", placeholder="例如：长安城中心")
            description = st.text_area("场景描述", placeholder="请输入该场景的环境描述...")

            submitted = st.form_submit_button("✅ 添加场景", use_container_width=True)
            if submitted:
                if not name or not name.strip():
                    st.error("场景名称不能为空")
                else:
                    new_scene = {
                        "id": str(uuid.uuid4()),
                        "name": name.strip(),
                        "location": location.strip(),
                        "description": description.strip(),
                    }
                    updated_scenes = scenes_list + [new_scene]
                    storage.update_project(project_id, {"scenes": updated_scenes})
                    st.success(f"场景「{new_scene['name']}」添加成功！")
                    st.rerun()

    st.markdown("---")

    # 场景列表展示
    if not scenes_list:
        st.info("暂无场景，请添加演出背景。")
        return

    st.subheader(f"场景列表（共 {len(scenes_list)} 个）")

    # 每行展示 2 个场景卡片
    cols_per_row = 2
    for i in range(0, len(scenes_list), cols_per_row):
        row_scenes = scenes_list[i : i + cols_per_row]
        cols = st.columns(cols_per_row)
        for idx, scene in enumerate(row_scenes):
            with cols[idx]:
                with st.container(border=True):
                    st.markdown(f"**{scene.get('name', '未命名场景')}**")
                    st.caption(f"📍 地点：{scene.get('location') or '未设置'}")

                    desc = scene.get("description", "")
                    if desc:
                        st.write(desc)
                    else:
                        st.caption("暂无描述")

                    # 统计被多少个场次使用
                    usage_count = sum(1 for act in acts_list if act.get("scene_id") == scene["id"])
                    st.caption(f"🔗 被 {usage_count} 个场次使用")
=======
场景编排页面：优先展示后端 screenplay_json.scenes。

如果后端尚未生成结果，则保留原本本地场景管理的最小空状态提示。
"""

from __future__ import annotations

import streamlit as st

from frontend import backend_types as bt
from frontend.utils import storage


def _render_generated_scene(scene: dict, screenplay: dict) -> None:
    names = bt.character_name_map(screenplay)
    events = bt.event_title_map(screenplay)
    heading = scene.get("scene_heading", {}) or {}
    location = scene.get("location", {}) or {}

    with st.container(border=True):
        st.markdown(f"**{heading.get('sequence', '-')}. {scene.get('title', '未命名场景')}**")
        st.caption(f"场景标题文本：{heading.get('text', '无')}")
        st.caption(
            f"地点：{location.get('name') or heading.get('location', '未设置')} | "
            f"时间：{location.get('time') or heading.get('time_of_day', '未设置')} | "
            f"内外景：{location.get('interior_exterior') or heading.get('interior_exterior', '未设置')}"
        )
        st.write("出场角色：" + ("、".join(names.get(cid, cid) for cid in bt.as_list(scene.get("characters"))) or "暂无"))
        st.write("戏剧目的：" + "；".join(str(item) for item in bt.as_list(scene.get("dramatic_purpose"))))
        st.write("关联事件：" + ("、".join(events.get(eid, eid) for eid in bt.as_list(scene.get("related_events"))) or "暂无"))

        c1, c2 = st.columns(2)
        with c1:
            if st.button("编辑", key=f"scene_page_edit_{scene.get('id')}", use_container_width=True):
                st.session_state.selected_scene = scene.get("id")
                st.info("TODO：等待后端提供保存场景编辑接口。")
        with c2:
            if st.button("删除", key=f"scene_page_delete_{scene.get('id')}", use_container_width=True):
                st.warning("请再次确认删除。当前删除不会回写后端。")

        with st.expander("展开查看 action / content_blocks / dialogue / source_refs", expanded=False):
            st.markdown("**Action**")
            for action in bt.as_list(scene.get("action")):
                st.write(action)
            st.markdown("**Content Blocks**")
            st.json(scene.get("content_blocks", []))
            st.markdown("**Dialogue**")
            st.json(scene.get("dialogue", []))
            st.markdown("**Source Refs**")
            st.json(scene.get("source_refs", []))


def render(project: dict):
    """渲染场景编排页面。"""
    st.header("场景编排")
    st.caption("展示生成后的文学剧本 scene，可展开查看正文和引用。")
    st.markdown("---")

    screenplay = bt.screenplay_from_artifacts(project)
    generated_scenes = screenplay.get("scenes", []) if screenplay else []

    if generated_scenes:
        for scene in generated_scenes:
            _render_generated_scene(scene, screenplay)
        return

    project_id = project.get("id")
    scenes_list = project.get("scenes", [])
    st.info("还没有后端生成的场景数据。")

    if not scenes_list:
        st.caption("本地也暂无场景。请先导入章节并完成生成。")
        return

    for scene in scenes_list:
        with st.container(border=True):
            st.markdown(f"**{scene.get('name', '未命名场景')}**")
            st.caption(f"地点：{scene.get('location') or '未设置'}")
            st.write(scene.get("description") or "暂无描述")
            if st.button("删除本地场景", key=f"delete_local_scene_{scene.get('id')}", use_container_width=True):
                updated = [item for item in scenes_list if item.get("id") != scene.get("id")]
                storage.update_project(project_id, {"scenes": updated})
                st.rerun()
>>>>>>> 7be98a4 (feat: add screenplay schema design and JSON/YAML definitions)

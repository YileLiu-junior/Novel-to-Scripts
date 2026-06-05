"""
scenes.py
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

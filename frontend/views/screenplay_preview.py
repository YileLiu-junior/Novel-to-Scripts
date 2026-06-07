# -*- coding: utf-8 -*-
"""
screenplay_preview.py
剧本预览页面：根据当前 frontend_data 中的人物、场景、事件数据生成前端预览文本。
"""

from __future__ import annotations

from html import escape
from typing import Any

import streamlit as st

from frontend import api_client, backend_types as bt


def _load_fd(project: dict) -> dict | None:
    """读取 frontend_data，如果不存在则尝试初始化。"""
    backend_pid = project.get("backend_project_id")
    if not backend_pid:
        return None
    # 优先 GET 已有数据
    try:
        fd = api_client.get_frontend_data(backend_pid)
        if fd and (fd.get("characters") or fd.get("scenes") or fd.get("plots")):
            st.session_state["_sp_characters"] = fd.get("characters", [])
            st.session_state["_sp_scenes"] = fd.get("scenes", [])
            st.session_state["_sp_plots"] = fd.get("plots", [])
            st.session_state["_sp_char_relations"] = fd.get("character_relations", [])
            st.session_state["_sp_causal_relations"] = fd.get("causal_relations", [])
            return fd
    except api_client.ApiClientError:
        pass
    # GET 失败或数据为空，尝试初始化
    try:
        fd = api_client.init_frontend_data(backend_pid)
        st.session_state["_sp_characters"] = fd.get("characters", [])
        st.session_state["_sp_scenes"] = fd.get("scenes", [])
        st.session_state["_sp_plots"] = fd.get("plots", [])
        st.session_state["_sp_char_relations"] = fd.get("character_relations", [])
        st.session_state["_sp_causal_relations"] = fd.get("causal_relations", [])
        return fd
    except api_client.ApiClientError:
        return None


def _build_character_name_map(characters: list) -> dict[str, str]:
    """建立 char_id 到人物姓名的显示映射。"""
    result: dict[str, str] = {}
    for character in characters:
        if not isinstance(character, dict):
            continue
        character_id = str(character.get("id") or "").strip()
        name = str(character.get("name") or "").strip()
        if character_id:
            result[character_id] = name or character_id
    return result


def _scene_sequence(scene: dict) -> int:
    """把 scene.sequence 归一成整数。"""
    try:
        return int(scene.get("sequence", 0))
    except (TypeError, ValueError):
        return 0


def _scene_title(scene: dict) -> str:
    """获取场景标题，按优先级尝试多个字段。"""
    title = str(scene.get("title") or "").strip()
    if title:
        return title
    heading_text = str(scene.get("heading_text") or "").strip()
    if heading_text:
        return heading_text
    location = str(scene.get("location") or "").strip()
    if location:
        return location
    return str(scene.get("id", "未命名场景"))


def _content_block_text(block: dict, character_name_map: dict[str, str]) -> str:
    """把 content_block 转成人可读文本。"""
    text = str(block.get("text") or block.get("line") or "").strip()
    if not text:
        return ""
    block_type = str(block.get("block_type") or block.get("type") or "action").strip().lower()
    if block_type == "dialogue":
        character_id = str(block.get("character_id") or block.get("speaker") or "").strip()
        speaker = character_name_map.get(character_id, "")
        if speaker:
            # 如果文本已经以人物名开头，不重复拼接
            if text.startswith(f"{speaker}：") or text.startswith(f"{speaker}:"):
                return f"【对白】{text}"
            return f"【对白】{speaker}：{text}"
        return f"【对白】{text}"
    if block_type == "action":
        return f"【动作】{text}"
    return f"【{block_type}】{text}"


def _generate_preview_text(
    characters: list,
    scenes: list,
    plots: list,
    character_name_map: dict[str, str],
) -> str:
    """根据人物、场景、事件数据生成剧本预览文本。"""
    lines: list[str] = []

    # 1. 人物介绍
    if characters:
        lines.append("=" * 40)
        lines.append("人物介绍")
        lines.append("=" * 40)
        lines.append("")
        for char in characters:
            if not isinstance(char, dict):
                continue
            name = str(char.get("name") or "未命名").strip()
            char_id = str(char.get("id") or "").strip()
            description = str(char.get("description") or "").strip()
            narrative_role = str(char.get("narrative_role") or "").strip()
            aliases = char.get("aliases") or []
            if isinstance(aliases, list):
                aliases_str = "、".join(str(a).strip() for a in aliases if str(a).strip())
            else:
                aliases_str = ""
            voice = char.get("voice_profile", {})
            rhythm = str(voice.get("rhythm") or "").strip() if isinstance(voice, dict) else ""
            diction = str(voice.get("diction") or "").strip() if isinstance(voice, dict) else ""

            parts = [name]
            if narrative_role:
                parts.append(f"（{narrative_role}）")
            info_parts = []
            if description:
                info_parts.append(description)
            if aliases_str:
                info_parts.append(f"别名：{aliases_str}")
            if rhythm:
                info_parts.append(f"语言节奏：{rhythm}")
            if diction:
                info_parts.append(f"语言风格：{diction}")

            lines.append("".join(parts))
            if info_parts:
                lines.append("  " + "；".join(info_parts))
            lines.append("")

    # 2. 建立 event_id -> plot 映射
    plot_map: dict[str, dict] = {}
    for plot in plots:
        if isinstance(plot, dict):
            pid = str(plot.get("id") or "").strip()
            if pid:
                plot_map[pid] = plot

    # 3. 按场景顺序展示
    sorted_scenes = sorted(
        [s for s in scenes if isinstance(s, dict)],
        key=_scene_sequence,
    )

    if sorted_scenes:
        lines.append("=" * 40)
        lines.append("剧本正文")
        lines.append("=" * 40)
        lines.append("")

    for scene in sorted_scenes:
        scene_id = str(scene.get("id") or "").strip()
        title = _scene_title(scene)
        location = str(scene.get("location") or "").strip()
        time = str(scene.get("time") or "").strip()

        # 场景标题
        lines.append(f"▶ 场景：{title}")
        if location or time:
            meta = []
            if location:
                meta.append(f"地点：{location}")
            if time:
                meta.append(f"时间：{time}")
            lines.append(f"  ({' / '.join(meta)})")
        lines.append("")

        # 场景中的 content_blocks
        content_blocks = [b for b in bt.as_list(scene.get("content_blocks")) if isinstance(b, dict)]
        if content_blocks:
            for block in content_blocks:
                text = _content_block_text(block, character_name_map)
                if text:
                    lines.append(text)
            lines.append("")
        else:
            # fallback: 使用 scene.action
            actions = bt.as_list(scene.get("action"))
            if actions:
                for action in actions:
                    if str(action).strip():
                        lines.append(f"【动作】{action}")
                lines.append("")

        # 关联事件
        related_events = [str(item).strip() for item in bt.as_list(scene.get("related_events")) if str(item).strip()]
        for event_id in related_events:
            plot = plot_map.get(event_id)
            if plot:
                event_title = str(plot.get("title") or event_id).strip()
                lines.append(f"  ◆ 事件：{event_title}")
                # 事件的 content_blocks
                plot_blocks = [b for b in bt.as_list(plot.get("content_blocks")) if isinstance(b, dict)]
                if plot_blocks:
                    for block in plot_blocks:
                        text = _content_block_text(block, character_name_map)
                        if text:
                            lines.append(f"  {text}")
                else:
                    plot_actions = bt.as_list(plot.get("actions") or plot.get("action"))
                    for action in plot_actions:
                        if str(action).strip():
                            lines.append(f"  【动作】{action}")
                lines.append("")

    return "\n".join(lines)


def _render_wrapped_text(text: str) -> None:
    """用可换行 HTML 展示长文本。"""
    safe_text = escape(text)
    st.markdown(
        f"""
        <div id="preview-text" style="
            white-space: pre-wrap;
            word-break: break-word;
            overflow-wrap: anywhere;
            max-width: 100%;
            box-sizing: border-box;
            line-height: 1.8;
            font-size: 14px;
            padding: 12px;
            background-color: #f8f9fa;
            border-radius: 8px;
        ">{safe_text}</div>
        """,
        unsafe_allow_html=True,
    )


def render(project: dict) -> None:
    """渲染剧本预览页面。"""
    st.header("剧本预览")

    backend_pid = project.get("backend_project_id")
    if not backend_pid:
        st.info("暂无后端项目关联，请先创建项目并导入原文。")
        return

    # 加载数据
    fd = _load_fd(project)
    if fd is None:
        st.warning("正在初始化可编辑数据...")
        return

    characters = st.session_state.get("_sp_characters", fd.get("characters", []))
    scenes = st.session_state.get("_sp_scenes", fd.get("scenes", []))
    plots = st.session_state.get("_sp_plots", fd.get("plots", []))

    if not scenes:
        st.info("暂无可预览内容，请先生成结构化剧本。")
        return

    character_name_map = _build_character_name_map(characters)

    # 生成预览文本
    preview_text = _generate_preview_text(characters, scenes, plots, character_name_map)

    # 操作按钮
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("刷新预览", use_container_width=True):
            st.rerun()
    with col2:
        st.download_button(
            label="下载 TXT",
            data=preview_text,
            file_name=f"{project.get('name', '剧本')}_预览.txt",
            mime="text/plain",
            use_container_width=True,
        )
    with col3:
        # 复制全文按钮（通过 JavaScript）
        st.markdown(
            f"""
            <button onclick="navigator.clipboard.writeText(document.getElementById('preview-text').innerText)"
                style="width: 100%; padding: 8px; border-radius: 4px; border: 1px solid #ccc; background: white; cursor: pointer;">
                复制全文
            </button>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # 显示预览文本
    _render_wrapped_text(preview_text)

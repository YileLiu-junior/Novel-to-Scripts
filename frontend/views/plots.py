# -*- coding: utf-8 -*-
"""
plots.py
事件管理页面：展示和编辑 frontend_data 中的 plots，并从 scenes 动态补充
action、content_blocks、source_scene_ids 等可读剧情内容。
"""

from __future__ import annotations

from copy import deepcopy
from html import escape
from typing import Any

import streamlit as st

from frontend import api_client, backend_types as bt


def _next_event_id(events_list: list) -> str:
    """生成下一个 event_XXX ID，保持现有自动编号规则。"""
    max_num = 0
    for event in events_list:
        event_id = event.get("id", "")
        if event_id.startswith("event_"):
            try:
                max_num = max(max_num, int(event_id.split("_")[1]))
            except (ValueError, IndexError):
                pass
    return f"event_{max_num + 1:03d}"


def _check_event_title_unique(title: str, current_id: str, events_list: list) -> bool:
    """校验事件标题唯一性，编辑当前事件时排除自身。"""
    normalized = title.strip().lower()
    for event in events_list:
        if event.get("id") != current_id and event.get("title", "").strip().lower() == normalized:
            return False
    return True


def _as_text_list(value: Any) -> list[str]:
    """把 action/actions 字段压成字符串列表。"""
    if isinstance(value, str):
        return [line.strip() for line in value.splitlines() if line.strip()]
    return [str(item).strip() for item in bt.as_list(value) if str(item).strip()]


def _dedupe(items: list[Any]) -> list[Any]:
    """按 repr 去重，保留原顺序。"""
    seen: set[str] = set()
    result: list[Any] = []
    for item in items:
        marker = repr(item)
        if marker in seen:
            continue
        seen.add(marker)
        result.append(item)
    return result


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


def _build_scene_title_map(scenes: list) -> dict[str, str]:
    """建立 scene_id 到场景标题的显示映射。"""
    result: dict[str, str] = {}
    for scene in sorted(scenes, key=lambda item: item.get("sequence", 0) if isinstance(item, dict) else 0):
        if not isinstance(scene, dict):
            continue
        scene_id = str(scene.get("id") or "").strip()
        title = str(scene.get("title") or scene.get("heading_text") or "").strip()
        if scene_id:
            result[scene_id] = title or scene_id
    return result


def _scene_content_blocks(scene: dict) -> list[dict]:
    """只读取 scene.content_blocks；scene.action 是摘要 fallback，不混入正文内容块。"""
    blocks = [dict(block) for block in bt.as_list(scene.get("content_blocks")) if isinstance(block, dict)]
    return blocks


def _content_block_key(block: dict) -> tuple[str, str]:
    """为内容块生成稳定去重 key：优先用 id，否则用 block_type + text。"""
    block_id = str(block.get("id") or "").strip()
    if block_id:
        return ("id", block_id)
    block_type = str(block.get("block_type") or block.get("type") or "action").strip().lower()
    text = str(block.get("text") or block.get("line") or "").strip()
    return ("body", f"{block_type}:{text}")


def _dedupe_content_blocks(blocks: list) -> list[dict]:
    """按出现顺序保留内容块，并避免 scene 合并时重复渲染同一块。"""
    result: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for block in blocks:
        if not isinstance(block, dict):
            continue
        key = _content_block_key(block)
        if key in seen:
            continue
        seen.add(key)
        result.append(block)
    return result


def _scene_sequence(scene: dict) -> int:
    """把 scene.sequence 归一成整数，避免字符串序号影响排序稳定性。"""
    try:
        return int(scene.get("sequence", 0))
    except (TypeError, ValueError):
        return 0


def _merge_plots_with_scene_details(plots: list, scenes: list) -> list[dict]:
    """把 scenes 中与 related_events 关联的动作、内容块、来源场景动态合并到事件。"""
    merged: dict[str, dict] = {}
    order: list[str] = []

    for plot in plots:
        if not isinstance(plot, dict):
            continue
        event_id = str(plot.get("id") or "").strip()
        if not event_id:
            continue
        merged[event_id] = deepcopy(plot)
        merged[event_id].setdefault("actions", _as_text_list(plot.get("actions") or plot.get("action")))
        merged[event_id].setdefault(
            "fallback_actions",
            _as_text_list(plot.get("fallback_actions") or plot.get("actions") or plot.get("action")),
        )
        merged[event_id].setdefault("content_blocks", bt.as_list(plot.get("content_blocks")))
        merged[event_id].setdefault("source_scene_ids", bt.as_list(plot.get("source_scene_ids")))
        merged[event_id].setdefault("characters", bt.as_list(plot.get("characters")))
        order.append(event_id)

    sorted_scenes = sorted(
        [scene for scene in scenes if isinstance(scene, dict)],
        key=_scene_sequence,
    )
    for scene in sorted_scenes:
        scene_id = str(scene.get("id") or "").strip()
        related_events = [str(item).strip() for item in bt.as_list(scene.get("related_events")) if str(item).strip()]
        if not related_events:
            continue

        scene_actions = _as_text_list(scene.get("actions") or scene.get("action"))
        scene_blocks = _scene_content_blocks(scene)
        scene_characters = bt.as_list(scene.get("characters"))

        for event_id in related_events:
            if event_id not in merged:
                merged[event_id] = {
                    "id": event_id,
                    "title": str(scene.get("title") or f"事件 {event_id}"),
                    "summary": "",
                    "description": "",
                    "characters": [],
                    "type": "",
                    "importance": "",
                    "source_refs": [],
                    "actions": [],
                    "fallback_actions": [],
                    "content_blocks": [],
                    "source_scene_ids": [],
                }
                order.append(event_id)

            event = merged[event_id]
            event["actions"] = _dedupe(bt.as_list(event.get("actions")) + scene_actions)
            event["fallback_actions"] = _dedupe(bt.as_list(event.get("fallback_actions")) + scene_actions)
            event["content_blocks"] = _dedupe_content_blocks(bt.as_list(event.get("content_blocks")) + scene_blocks)
            event["source_scene_ids"] = _dedupe(bt.as_list(event.get("source_scene_ids")) + ([scene_id] if scene_id else []))
            event["characters"] = _dedupe(bt.as_list(event.get("characters")) + scene_characters)

    for event in merged.values():
        event["content_blocks"] = _dedupe_content_blocks(bt.as_list(event.get("content_blocks")))

    return [merged[event_id] for event_id in order if event_id in merged]


def _text_has_speaker_prefix(text: str, speaker: str) -> bool:
    """判断对白文本是否已经以人物名开头，避免重复拼接。"""
    if not speaker:
        return False
    compact_text = text.strip()
    compact_speaker = speaker.strip()
    return compact_text.startswith(f"{compact_speaker}:") or compact_text.startswith(f"{compact_speaker}：")


def _content_block_text(block: dict, character_name_map: dict[str, str]) -> str:
    """把 content_block 转成人可读文本，dialogue 尽量映射 character_id 为人物姓名。"""
    text = str(block.get("text") or block.get("line") or "").strip()
    if not text:
        return ""
    block_type = str(block.get("block_type") or block.get("type") or "action").strip().lower()
    if block_type == "dialogue":
        character_id = str(block.get("character_id") or block.get("speaker") or "").strip()
        speaker = character_name_map.get(character_id, "")
        if speaker and _text_has_speaker_prefix(text, speaker):
            return f"【对白】{text}"
        prefix = f"【对白】{speaker}：" if speaker else "【对白】"
        return f"{prefix}{text}"
    if block_type == "action":
        return f"【动作】{text}"
    return f"【{block_type}】{text}"


def _content_blocks_to_text(blocks: list) -> str:
    """把 content_blocks 转为可编辑文本，每行一条。"""
    lines = []
    for block in bt.as_list(blocks):
        if isinstance(block, dict):
            text = str(block.get("text") or block.get("line") or "").strip()
        else:
            text = str(block).strip()
        if text:
            lines.append(text)
    return "\n".join(lines)


def _text_to_content_blocks(text: str, original_blocks: list | None = None) -> list[dict]:
    """把 textarea 文本保存回 content_blocks，尽量保留原块类型和 ID。"""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    originals = [block for block in bt.as_list(original_blocks) if isinstance(block, dict)]
    result = []
    for index, line in enumerate(lines):
        block = dict(originals[index]) if index < len(originals) else {}
        block.setdefault("id", f"block_{index + 1:03d}")
        block.setdefault("block_type", "action")
        block["text"] = line
        result.append(block)
    return result


def _save_to_backend(project: dict, plots: list, causal_relations: list) -> bool:
    """保存事件和因果关系，同时原样带回其他 frontend_data 分区。"""
    backend_pid = project.get("backend_project_id")
    if not backend_pid:
        st.error("无法保存：缺少后端项目 ID")
        return False
    try:
        with st.spinner("保存中..."):
            result = api_client.save_frontend_data(
                backend_pid,
                {
                    "characters": st.session_state.get("_fd_characters", []),
                    "character_relations": st.session_state.get("_fd_char_relations", []),
                    "scenes": st.session_state.get("_fd_scenes", []),
                    "scene_relations": st.session_state.get("_fd_scene_relations", []),
                    "plots": plots,
                    "causal_relations": causal_relations,
                },
            )
            st.session_state["_fd_plots"] = result.get("plots", plots)
            st.session_state["_fd_causal_relations"] = result.get("causal_relations", causal_relations)
            st.success("保存成功")
            return True
    except api_client.ApiClientError as exc:
        st.error(f"保存失败：{exc.message}")
        return False


def _load_fd(project: dict) -> dict | None:
    """初始化并读取 frontend_data，缓存页面需要的分区。"""
    backend_pid = project.get("backend_project_id")
    if not backend_pid:
        return None
    try:
        fd = api_client.init_frontend_data(backend_pid)
    except api_client.ApiClientError:
        return None
    st.session_state["_fd_characters"] = fd.get("characters", [])
    st.session_state["_fd_char_relations"] = fd.get("character_relations", [])
    st.session_state["_fd_scenes"] = fd.get("scenes", [])
    st.session_state["_fd_scene_relations"] = fd.get("scene_relations", [])
    st.session_state["_fd_plots"] = fd.get("plots", [])
    st.session_state["_fd_causal_relations"] = fd.get("causal_relations", [])
    return fd


def _short_text(value: str, limit: int = 100) -> str:
    """把事件描述压缩到卡片可读长度，避免撑破布局。"""
    text = value.strip() if isinstance(value, str) else ""
    if len(text) <= limit:
        return text
    return text[:limit] + "..."


def _render_wrapped_text(text: str) -> None:
    """用可换行 HTML 展示长文本，避免撑破页面。"""
    safe_text = escape(text)
    st.markdown(
        f"""
        <div style="
            white-space: pre-wrap;
            word-break: break-word;
            overflow-wrap: anywhere;
            max-width: 100%;
            box-sizing: border-box;
        ">{safe_text}</div>
        """,
        unsafe_allow_html=True,
    )


def _render_event_item(
    event: dict,
    project: dict,
    plots_list: list,
    causal_relations: list,
    character_name_map: dict[str, str],
    scene_title_map: dict[str, str],
) -> None:
    """渲染单条事件卡片，展示从场景补充来的动作和内容块。"""
    event_id = event.get("id", "")
    title = event.get("title") or "未命名事件"
    description = event.get("summary") or event.get("description") or "暂无描述"
    event_type = event.get("type", "")
    importance = event.get("importance", "")
    source_refs = bt.ref_text(event.get("source_refs", []))
    content_blocks = [block for block in bt.as_list(event.get("content_blocks")) if isinstance(block, dict)]
    fallback_actions = _as_text_list(event.get("fallback_actions") or event.get("actions") or event.get("action"))
    source_scene_ids = [str(item) for item in bt.as_list(event.get("source_scene_ids")) if item]
    source_scene_titles = [scene_title_map.get(scene_id, scene_id) for scene_id in source_scene_ids]

    with st.container(border=True):
        st.markdown(f"**{title}**")
        st.caption(f"ID: {event_id}")

        meta = []
        if event_type:
            meta.append(f"事件类型：{event_type}")
        if importance:
            meta.append(f"重要程度：{importance}")
        if meta:
            st.caption(" | ".join(meta))

        st.write(_short_text(description))
        if source_refs:
            st.caption(f"来源信息：{source_refs}")
        if source_scene_titles:
            st.caption("来源场景：" + "、".join(source_scene_titles))

        if content_blocks:
            with st.expander("内容块", expanded=False):
                lines = [
                    line
                    for line in (_content_block_text(block, character_name_map) for block in content_blocks)
                    if line
                ]
                _render_wrapped_text("\n".join(lines) if lines else "暂无内容块文本")
        elif fallback_actions:
            with st.expander("事件摘要", expanded=False):
                _render_wrapped_text("\n".join(fallback_actions))

        c1, c2 = st.columns(2)
        with c1:
            if st.button("编辑", key=f"plot_edit_{event_id}", use_container_width=True):
                st.session_state["editing_plot_id"] = event_id
                st.rerun()

        with c2:
            confirm_key = f"plot_delete_confirm_{event_id}"
            if st.session_state.get(confirm_key):
                if st.button("确认删除", key=f"plot_delete_yes_{event_id}", type="primary", use_container_width=True):
                    updated_plots = [item for item in plots_list if item.get("id") != event_id]
                    if _save_to_backend(project, updated_plots, causal_relations):
                        st.session_state.pop(confirm_key, None)
                        if st.session_state.get("editing_plot_id") == event_id:
                            st.session_state.pop("editing_plot_id", None)
                        st.success(f"事件《{title}》已删除。")
                        st.rerun()
                if st.button("取消", key=f"plot_delete_no_{event_id}", use_container_width=True):
                    st.session_state.pop(confirm_key, None)
                    st.rerun()
            elif st.button("删除", key=f"plot_delete_{event_id}", use_container_width=True):
                st.session_state[confirm_key] = True
                st.rerun()


def _upsert_plot(plots_list: list, updated_event: dict) -> list:
    """更新已有事件；若该事件来自 scene.related_events 动态补充，则追加到 plots。"""
    found = False
    updated = []
    for item in plots_list:
        if item.get("id") == updated_event.get("id"):
            updated.append(updated_event)
            found = True
        else:
            updated.append(item)
    if not found:
        updated.append(updated_event)
    return updated


def _render_event_editor(event: dict, project: dict, plots_list: list, causal_relations: list) -> None:
    """渲染事件编辑表单；可编辑 actions/content_blocks/type/importance。"""
    event_id = event.get("id", "")
    title = event.get("title", "")
    summary = event.get("summary") or event.get("description") or ""
    event_type = event.get("type", "")
    importance = event.get("importance", "")
    actions_text = "\n".join(_as_text_list(event.get("actions") or event.get("action")))
    content_blocks_text = _content_blocks_to_text(event.get("content_blocks"))

    with st.container(border=True):
        st.markdown(f"#### 编辑事件（ID: {event_id}）")
        st.caption("ID 不可编辑")

        with st.form(f"edit_plot_form_{event_id}"):
            title_val = st.text_input("事件标题", value=title)
            description_val = st.text_area("事件描述", value=summary, height=120)
            actions_val = st.text_area("事件动作（每行一条）", value=actions_text, height=140)
            content_blocks_val = st.text_area("内容块文本（每行一条）", value=content_blocks_text, height=160)
            event_type_val = st.text_input("事件类型", value=event_type)
            importance_val = st.text_input("重要程度", value=importance)

            c1, c2 = st.columns(2)
            with c1:
                submitted = st.form_submit_button("保存", use_container_width=True)
            with c2:
                cancelled = st.form_submit_button("取消", use_container_width=True)

            if submitted:
                clean_title = title_val.strip()
                if not clean_title:
                    st.error("事件标题不能为空")
                    return
                if not _check_event_title_unique(clean_title, event_id, plots_list):
                    st.error(f"事件标题《{clean_title}》已存在，请使用其他标题。")
                    return

                updated_event = dict(event)
                updated_event["title"] = clean_title
                updated_event["description"] = description_val.strip()
                updated_event["summary"] = description_val.strip()
                updated_event["actions"] = _as_text_list(actions_val)
                updated_event["content_blocks"] = _text_to_content_blocks(content_blocks_val, event.get("content_blocks"))
                updated_event["type"] = event_type_val.strip()
                updated_event["importance"] = importance_val.strip()

                if _save_to_backend(project, _upsert_plot(plots_list, updated_event), causal_relations):
                    st.session_state.pop("editing_plot_id", None)
                    st.success(f"事件《{clean_title}》保存成功！")
                    st.rerun()

            if cancelled:
                st.session_state.pop("editing_plot_id", None)
                st.rerun()


def _render_add_event(project: dict, plots_list: list, causal_relations: list) -> None:
    """渲染添加事件表单；新增事件保持字段一致。"""
    backend_pid = project.get("backend_project_id", "")
    show_form_key = f"show_add_event_form_{backend_pid}"
    if show_form_key not in st.session_state:
        st.session_state[show_form_key] = False

    if not st.session_state.get(show_form_key, False):
        if st.button("添加事件", key=f"btn_add_event_{backend_pid}", use_container_width=True):
            st.session_state[show_form_key] = True
            st.rerun()
        return

    with st.container(border=True):
        st.markdown("#### 添加新事件")
        with st.form(f"add_event_form_{backend_pid}", clear_on_submit=True):
            title = st.text_input("事件标题", placeholder="例如：主角发现真相")
            description = st.text_area("事件描述", placeholder="请输入该事件的详细描述...", height=120)
            actions = st.text_area("事件动作（每行一条）", height=120)
            content_blocks = st.text_area("内容块文本（每行一条）", height=140)
            event_type = st.text_input("事件类型", placeholder="例如：转折、高潮、铺垫")
            importance = st.text_input("重要程度", placeholder="例如：高、中、低")

            c1, c2 = st.columns(2)
            with c1:
                submitted = st.form_submit_button("添加", use_container_width=True)
            with c2:
                cancelled = st.form_submit_button("取消", use_container_width=True)

            if submitted:
                clean_title = title.strip()
                if not clean_title:
                    st.error("事件标题不能为空")
                    return
                if not _check_event_title_unique(clean_title, "", plots_list):
                    st.error(f"事件标题《{clean_title}》已存在，请使用其他标题。")
                    return

                new_event = {
                    "id": _next_event_id(plots_list),
                    "title": clean_title,
                    "summary": description.strip(),
                    "description": description.strip(),
                    "actions": _as_text_list(actions),
                    "content_blocks": _text_to_content_blocks(content_blocks),
                    "source_scene_ids": [],
                    "characters": [],
                    "type": event_type.strip(),
                    "importance": importance.strip(),
                    "source_refs": [],
                }
                updated_plots = plots_list + [new_event]
                if _save_to_backend(project, updated_plots, causal_relations):
                    st.success(f"事件《{new_event['title']}》添加成功！")
                    st.session_state[show_form_key] = False
                    st.rerun()

            if cancelled:
                st.session_state[show_form_key] = False
                st.rerun()


def _render_causal_relations(plots_list: list, causal_relations: list) -> None:
    """展示事件之间的因果关系。"""
    st.markdown("---")
    st.subheader("因果关系")

    event_title_map = {
        item.get("id", ""): item.get("title", item.get("id", ""))
        for item in plots_list
        if item.get("id")
    }
    edges = bt.as_list(causal_relations)

    if not edges:
        st.info("暂无因果关系数据")
        return

    rows = []
    for edge in edges:
        from_id = edge.get("from", "")
        to_id = edge.get("to", "")
        rows.append(
            {
                "from": event_title_map.get(from_id, from_id) if from_id else "未知",
                "relation": edge.get("relation", ""),
                "to": event_title_map.get(to_id, to_id) if to_id else "未知",
                "description": edge.get("description", ""),
            }
        )

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


def render(project: dict) -> None:
    """渲染事件管理页面。"""
    st.header("事件管理")

    backend_pid = project.get("backend_project_id")
    if not backend_pid:
        st.info("暂无后端项目关联，请先创建项目并导入原文。")
        return

    fd = _load_fd(project)
    if fd is None:
        st.warning("正在初始化可编辑数据...")
        return

    plots = st.session_state.get("_fd_plots", fd.get("plots", []))
    scenes = st.session_state.get("_fd_scenes", fd.get("scenes", []))
    characters = st.session_state.get("_fd_characters", fd.get("characters", []))
    causal_relations = st.session_state.get("_fd_causal_relations", fd.get("causal_relations", []))

    enhanced_plots = _merge_plots_with_scene_details(plots, scenes)
    character_name_map = _build_character_name_map(characters)
    scene_title_map = _build_scene_title_map(scenes)

    if not enhanced_plots:
        st.info("暂无事件数据。请先生成结构化剧本，或手动添加事件。")

    editing_id = st.session_state.get("editing_plot_id")
    for event in enhanced_plots:
        if event.get("id") == editing_id:
            _render_event_editor(event, project, plots, causal_relations)
        else:
            _render_event_item(event, project, plots, causal_relations, character_name_map, scene_title_map)

    _render_add_event(project, plots, causal_relations)
    _render_causal_relations(enhanced_plots, causal_relations)

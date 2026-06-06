"""
export.py
<<<<<<< HEAD
剧本导出页面：将项目数据导出为结构化 YAML 格式剧本。
支持预览 YAML、下载 YAML 文件、下载 Schema 文档。
"""

import streamlit as st
from frontend.utils import exporter


def render(project: dict):
    """
    渲染剧本导出页面。
    :param project: 当前项目字典
    """
    st.header("📋 剧本导出")
    st.caption("将当前项目中的原文、人物、场景、场次整理为结构化 YAML 剧本文件，便于后续编辑、校验和二次创作。")
    st.markdown("---")

    acts_list = project.get("acts", []) or []

    # 如果没有场次，显示提示
    if not acts_list:
        st.warning('当前项目暂无场次，请先在"场次"页面添加场次。')
        st.info("以下将导出基础项目结构（不含场次数据）。")

    st.markdown("---")

    # 生成 YAML
    yaml_text = exporter.generate_yaml(project)

    # YAML 预览区域
    st.subheader("📄 YAML 预览")
    st.code(yaml_text, language="yaml")

    st.markdown("---")

    # 下载按钮区域
    st.subheader("📥 下载")

    col1, col2 = st.columns(2)

    with col1:
        # 下载剧本 YAML
        yaml_filename = exporter.get_download_filename(project)
        st.download_button(
            label="📥 下载剧本 YAML",
            data=yaml_text.encode("utf-8"),
            file_name=yaml_filename,
            mime="text/yaml",
            use_container_width=True,
        )

    with col2:
        # 下载 YAML Schema 文档
        schema_doc_path = _get_schema_doc_path()
        if schema_doc_path:
            with open(schema_doc_path, "r", encoding="utf-8") as f:
                schema_doc_content = f.read()
            st.download_button(
                label="📄 下载 YAML Schema 文档",
                data=schema_doc_content.encode("utf-8"),
                file_name="yaml_schema.md",
                mime="text/markdown",
                use_container_width=True,
            )
        else:
            st.warning("Schema 文档文件未找到。")


def _get_schema_doc_path() -> str | None:
    """
    获取 YAML Schema 文档的路径。
    :return: 文件绝对路径，不存在则返回 None
    """
    import os
    doc_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "docs", "yaml_schema.md"
    )
    if os.path.exists(doc_path):
        return doc_path
    return None
=======
生成结果页面：以 Tab 展示后端产出的 screenplay_json、YAML、文学剧本和审查报告。

页面只消费后端 artifact，不修复内容；编辑/删除暂存于前端状态，等待后端提供保存接口。
"""

from __future__ import annotations

import json
from typing import Any

import streamlit as st

from frontend import api_client
from frontend import backend_types as bt
from frontend.utils import storage


def _screenplay(project: dict) -> dict[str, Any]:
    data = project.get("screenplay_data") or st.session_state.get("screenplay_data") or {}
    return data if isinstance(data, dict) else {}


def _backend_project_id(project: dict) -> str | None:
    return project.get("backend_project_id") or st.session_state.get("backend_project_id")


def _refresh_results_from_api(project: dict, project_id: str) -> dict:
    """进入结果页时按当前 project_id 拉取最新 artifacts，避免展示旧缓存。"""
    updates: dict[str, Any] = {}
    errors: list[str] = []
    for artifact_type, key in (
        ("screenplay_json", "screenplay_data"),
        ("screenplay_yaml", "screenplay_yaml"),
        ("audit_report", "audit_report"),
        ("screenplay_rendered", "screenplay_rendered"),
    ):
        try:
            artifact = api_client.get_artifact(project_id, artifact_type)
            updates[key] = artifact.get("data")
        except api_client.ApiClientError as exc:
            errors.append(exc.message)
    try:
        rendered = api_client.get_rendered(project_id, "markdown")
        updates["rendered_markdown"] = rendered.get("content", "")
    except api_client.ApiClientError as exc:
        errors.append(exc.message)

    if updates:
        storage.update_project(project["id"], updates)
        project.update(updates)
        for key, value in updates.items():
            st.session_state[key] = value
    if errors and not updates:
        st.error("无法读取当前项目生成结果：" + "；".join(errors[:2]))
    return project


def _looks_like_fake_provider(project: dict, screenplay: dict[str, Any]) -> bool:
    haystack = json.dumps(screenplay, ensure_ascii=False) + str(project.get("rendered_markdown", ""))
    return "Fake Provider" in haystack or "fake provider" in haystack


def _safe_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, indent=2)


def _download_button_from_api(label: str, project_id: str, kind: str, format_name: str | None = None) -> None:
    try:
        if kind == "yaml":
            file_data = api_client.download_yaml(project_id)
        else:
            file_data = api_client.download_rendered(project_id, format_name or "markdown")
        st.download_button(
            label=label,
            data=file_data.content,
            file_name=file_data.filename,
            mime=file_data.media_type,
            use_container_width=True,
        )
    except api_client.ApiClientError as exc:
        st.warning(f"下载暂不可用：{exc.message}")


def _render_preview_tab(project: dict, project_id: str | None) -> None:
    markdown_text = project.get("rendered_markdown") or st.session_state.get("rendered_markdown") or ""
    if project_id and not markdown_text:
        try:
            rendered = api_client.get_rendered(project_id, "markdown")
            markdown_text = rendered.get("content", "")
        except api_client.ApiClientError:
            rendered_artifact = project.get("screenplay_rendered")
            if isinstance(rendered_artifact, dict):
                markdown_text = rendered_artifact.get("formats", {}).get("markdown", {}).get("content", "")

    if markdown_text:
        st.markdown(markdown_text)
    else:
        st.info("还没有文学剧本预览，请先完成生成。")

    col1, col2 = st.columns(2)
    if project_id:
        with col1:
            _download_button_from_api("下载 Markdown", project_id, "rendered", "markdown")
        with col2:
            _download_button_from_api("下载 TXT", project_id, "rendered", "text")


def _render_yaml_tab(project: dict, project_id: str | None) -> None:
    yaml_text = project.get("screenplay_yaml") or st.session_state.get("screenplay_yaml") or ""
    if yaml_text:
        st.code(yaml_text, language="yaml")
    else:
        st.info("还没有 YAML artifact，请先完成生成。")

    col1, col2, col3 = st.columns(3)
    with col1:
        if project_id:
            _download_button_from_api("下载 YAML", project_id, "yaml")
    with col2:
        if project_id and st.button("校验当前 YAML", use_container_width=True, disabled=not bool(yaml_text)):
            try:
                result = api_client.validate_yaml(project_id, yaml_text)
                findings = result.get("findings", [])
                if findings:
                    st.warning(f"发现 {len(findings)} 个校验问题。")
                    st.json(findings)
                else:
                    st.success("YAML 校验通过。")
            except api_client.ApiClientError as exc:
                st.error(exc.message)
    with col3:
        if project_id:
            try:
                schema = api_client.download_schema(project_id)
                st.download_button(
                    label="下载 Schema",
                    data=schema.get("schema_text", "").encode("utf-8"),
                    file_name="screenplay.schema.json",
                    mime=schema.get("content_type", "application/schema+json"),
                    use_container_width=True,
                )
            except api_client.ApiClientError as exc:
                st.warning(f"Schema 下载暂不可用：{exc.message}")


def _render_characters_tab(screenplay: dict[str, Any]) -> None:
    story_bible = screenplay.get("story_bible", {})
    characters = story_bible.get("characters", []) or []
    relationships = story_bible.get("relationship_edges", []) or []
    knowledge_states = story_bible.get("knowledge_states", []) or []
    names = bt.character_name_map(screenplay)

    if not characters:
        st.info("暂无角色数据。")
    else:
        cols_per_row = 3
        for start in range(0, len(characters) + 1, cols_per_row):
            cols = st.columns(cols_per_row)
            for index, col in enumerate(cols):
                item_index = start + index
                with col:
                    if item_index < len(characters):
                        char = characters[item_index]
                        with st.container(border=True):
                            st.markdown(f"**{char.get('name', '未命名角色')}**")
                            aliases = "、".join(bt.as_list(char.get("aliases"))) or "无"
                            voice = char.get("voice_profile", {})
                            if isinstance(voice, dict):
                                voice_text = "；".join(
                                    str(value) for value in voice.values() if value
                                ) or "暂无"
                            else:
                                voice_text = str(voice)
                            st.caption(f"别名：{aliases}")
                            st.caption(f"叙事功能：{char.get('narrative_role', '未设置')}")
                            st.caption(f"语言风格：{voice_text}")
                            st.caption(f"来源章节：{bt.ref_text(char.get('source_refs'))}")
                            c1, c2 = st.columns(2)
                            with c1:
                                if st.button("编辑", key=f"edit_generated_char_{char.get('id')}", use_container_width=True):
                                    st.session_state.selected_character = char.get("id")
                                    st.info("TODO：等待后端提供保存角色编辑接口。")
                            with c2:
                                if st.button("删除", key=f"delete_generated_char_{char.get('id')}", use_container_width=True):
                                    st.warning("删除仅影响当前前端显示；TODO：等待后端提供保存编辑接口。")
                    elif item_index == len(characters):
                        with st.container(border=True):
                            st.markdown("**添加人物**")
                            st.caption("点击后进入添加人物流程。")
                            if st.button("添加人物", key="add_generated_character", use_container_width=True):
                                st.info("TODO：等待后端提供保存新增角色接口。")

    st.subheader("关系")
    if relationships:
        rows = []
        for rel in relationships:
            rows.append(
                {
                    "from": names.get(rel.get("from_character_id"), rel.get("from_character_id", "")),
                    "to": names.get(rel.get("to_character_id"), rel.get("to_character_id", "")),
                    "type": rel.get("type", ""),
                    "state": rel.get("current_state", ""),
                }
            )
        st.table(rows)
    else:
        st.info("暂无关系数据。")

    with st.expander("知识状态", expanded=False):
        st.json(knowledge_states)


def _render_scenes_tab(screenplay: dict[str, Any]) -> None:
    scenes = screenplay.get("scenes", []) or []
    names = bt.character_name_map(screenplay)
    event_names = bt.event_title_map(screenplay)
    if not scenes:
        st.info("暂无场景数据。")
        return

    for scene in scenes:
        with st.container(border=True):
            heading = scene.get("scene_heading", {}) or {}
            location = scene.get("location", {}) or {}
            st.markdown(f"**{heading.get('sequence', '-')}. {scene.get('title', '未命名场景')}**")
            st.caption(f"场景标题：{heading.get('text', '无')}")
            st.caption(
                f"地点：{location.get('name') or heading.get('location', '未设置')} | "
                f"时间：{location.get('time') or heading.get('time_of_day', '未设置')} | "
                f"内外景：{location.get('interior_exterior') or heading.get('interior_exterior', '未设置')}"
            )
            st.write("出场角色：" + ("、".join(names.get(cid, cid) for cid in bt.as_list(scene.get("characters"))) or "暂无"))
            st.write("戏剧目的：" + "；".join(str(item) for item in bt.as_list(scene.get("dramatic_purpose"))))
            st.write("关联事件：" + ("、".join(event_names.get(eid, eid) for eid in bt.as_list(scene.get("related_events"))) or "暂无"))

            c1, c2 = st.columns([1, 1])
            with c1:
                if st.button("编辑", key=f"edit_scene_{scene.get('id')}", use_container_width=True):
                    st.session_state.selected_scene = scene.get("id")
                    st.info("TODO：等待后端提供保存场景编辑接口，当前只记录前端选择状态。")
            with c2:
                confirm_key = f"confirm_delete_scene_{scene.get('id')}"
                if st.button("删除", key=f"delete_scene_{scene.get('id')}", use_container_width=True):
                    st.session_state[confirm_key] = True
                if st.session_state.get(confirm_key):
                    st.warning("确认删除该场景？当前删除不会回写后端。")

            with st.expander("展开查看场景正文与引用", expanded=False):
                st.markdown("**Action**")
                for action in bt.as_list(scene.get("action")):
                    st.write(action)
                st.markdown("**Content Blocks**")
                st.json(scene.get("content_blocks", []))
                st.markdown("**Dialogue**")
                st.json(scene.get("dialogue", []))
                st.markdown("**Source Refs**")
                st.json(scene.get("source_refs", []))


def _render_plot_tab(screenplay: dict[str, Any]) -> None:
    events = screenplay.get("events", []) or []
    edges = screenplay.get("causal_graph", {}).get("edges", []) or []
    foreshadowing = screenplay.get("foreshadowing", []) or []
    plan = screenplay.get("adaptation_plan", {}) or {}
    event_names = bt.event_title_map(screenplay)

    st.subheader("事件时间线")
    if events:
        for event in events:
            st.markdown(f"- **{event.get('title', event.get('id'))}**：{event.get('summary', '')}")
    else:
        st.info("暂无事件数据。")

    st.subheader("因果关系")
    if edges:
        rows = [
            {
                "from": event_names.get(edge.get("from_event_id") or edge.get("from"), edge.get("from_event_id") or edge.get("from")),
                "to": event_names.get(edge.get("to_event_id") or edge.get("to"), edge.get("to_event_id") or edge.get("to")),
                "relation": edge.get("relation", ""),
                "explanation": edge.get("explanation", ""),
            }
            for edge in edges
        ]
        st.table(rows)
    else:
        st.info("暂无因果关系。")

    st.subheader("伏笔追踪")
    if foreshadowing:
        st.table(
            [
                {
                    "id": item.get("id"),
                    "description": item.get("description"),
                    "status": item.get("status"),
                    "setup": item.get("setup_event_id") or item.get("setup_scene_id"),
                    "payoff": item.get("payoff_event_id") or item.get("payoff_scene_id"),
                }
                for item in foreshadowing
            ]
        )
    else:
        st.info("暂无伏笔数据。")

    st.subheader("改编计划")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**保留事件**")
        st.json(plan.get("retained_events", []))
        st.markdown("**合并事件**")
        st.json(plan.get("merged_events", []))
    with col2:
        st.markdown("**删除/延后事件**")
        st.json(plan.get("deleted_or_deferred_events", []))
        st.markdown("**保护点**")
        st.json(plan.get("protected_elements", []))
    st.markdown("**场景规划**")
    st.json(plan.get("scene_plan", []))


def _render_audit_tab(screenplay: dict[str, Any], project: dict) -> None:
    audit = screenplay.get("audit_report") or project.get("audit_report") or {}
    if not isinstance(audit, dict):
        st.info("暂无审查报告。")
        return

    total = bt.warning_count(audit)
    if total == 0:
        st.success("暂无问题")
        return

    st.warning(f"发现 {total} 条审查提示。")
    labels = {
        "schema_warnings": "Schema 警告",
        "continuity_warnings": "连贯性警告",
        "dialogue_warnings": "对白警告",
        "unresolved_foreshadowing": "未兑现伏笔",
    }
    for key, label in labels.items():
        items = bt.as_list(audit.get(key))
        with st.expander(f"{label}（{len(items)}）", expanded=bool(items)):
            if items:
                st.json(items)
            else:
                st.caption("暂无问题")


def render(project: dict):
    """渲染生成结果页面。"""
    st.header("生成结果")
    st.caption("这里展示后端生成的可审查 adaptation artifacts。")
    st.markdown("---")

    project_id = _backend_project_id(project)
    if project_id:
        project = _refresh_results_from_api(project, project_id)
    screenplay = _screenplay(project)

    if not screenplay:
        st.warning("还没有 screenplay_json。请先在“原文”页面导入至少 3 章并完成生成。")
        return

    if _looks_like_fake_provider(project, screenplay):
        st.warning("当前为 Fake Provider 模式，内容为根据当前项目章节构造的模拟生成结果，不是真实 AI 创作。")

    tab_preview, tab_yaml, tab_characters, tab_scenes, tab_plot, tab_audit = st.tabs(
        ["文学剧本预览", "YAML 结构", "角色与关系", "场景编排", "情节与因果", "审查报告"]
    )
    with tab_preview:
        _render_preview_tab(project, project_id)
    with tab_yaml:
        _render_yaml_tab(project, project_id)
    with tab_characters:
        _render_characters_tab(screenplay)
    with tab_scenes:
        _render_scenes_tab(screenplay)
    with tab_plot:
        _render_plot_tab(screenplay)
    with tab_audit:
        _render_audit_tab(screenplay, project)
>>>>>>> 7be98a4 (feat: add screenplay schema design and JSON/YAML definitions)

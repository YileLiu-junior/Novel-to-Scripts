# -*- coding: utf-8 -*-
"""
export.py
生成结果页面：仅展示 YAML 结构预览及相关操作。

其他生成内容（文学剧本、角色、场景、情节、审查报告）已拆分到独立页面，
通过左侧导航访问。
"""

from __future__ import annotations

import json
import logging
from typing import Any

import streamlit as st

from frontend import api_client, backend_types as bt
from frontend.utils import data_loader

logger = logging.getLogger(__name__)


def _looks_like_fake_provider(project: dict) -> bool:
    """检测当前项目数据是否来自 Fake Provider（模拟数据）。"""
    haystack = json.dumps(project, ensure_ascii=False)
    return "Fake Provider" in haystack or "fake provider" in haystack


def _render_evidence_tab(screenplay: dict) -> None:
    """展示 StoryOntology V1.5 改编证据，缺少 enriched 字段时显示空态。"""
    if not screenplay:
        st.info("暂无改编证据，请先生成结构化剧本。")
        return

    events = bt.as_list(screenplay.get("events"))
    plan = screenplay.get("adaptation_plan", {})
    complete_events = [event for event in events if isinstance(event, dict) and event.get("complete_event")]
    st.subheader(f"完整事件（{len(complete_events)}个）")
    problem_count = 0
    for event in complete_events:
        status = bt.event_planner_status(event, plan if isinstance(plan, dict) else {})
        if status != "已保护" and event.get("must_keep_together"):
            problem_count += 1
        with st.container(border=True):
            st.markdown(f"**{event.get('title', event.get('id'))}**")
            st.caption(f"{event.get('id')}｜{event.get('event_type', '')}｜{status}")
            if event.get("conflict_axis"):
                st.write(f"冲突轴：{event.get('conflict_axis')}")
            flow = bt.as_list(event.get("event_flow"))
            if flow:
                st.write("事件流：" + " → ".join(str(item) for item in flow))
            st.caption(bt.ref_text(event.get("source_refs", [])))
    if problem_count:
        st.warning(f"{problem_count} 个标记为不可拆分的完整事件在改编计划中被拆散或遗漏，请在审查报告中查看详情。")
    if not complete_events:
        st.info("暂无完整事件证据。")

    st.subheader("冲突轴")
    conflicts = bt.conflict_pool(screenplay)
    if conflicts:
        for item in conflicts:
            st.write(f"**{item.get('conflict_axis', item.get('id'))}**")
            st.caption(bt.ref_text(item.get("source_refs", [])))
    else:
        st.info("暂无冲突轴证据。")

    st.subheader("一致性锚点")
    anchors = bt.continuity_anchors(screenplay)
    if anchors:
        for item in anchors:
            st.write(f"[{item.get('anchor_type')}] {item.get('summary')}")
            st.caption(bt.ref_text(item.get("source_refs", [])))
    else:
        st.info("暂无一致性锚点。")

    st.subheader("关系与知情差")
    bible = screenplay.get("story_bible", {})
    if isinstance(bible, dict):
        st.write("关系：")
        for edge in bt.as_list(bible.get("relationship_edges")):
            if isinstance(edge, dict):
                st.write(f"{edge.get('from')} → {edge.get('to')}｜{edge.get('type')}｜{edge.get('current_state', '')}")
        st.write("知情差：")
        for state in bt.as_list(bible.get("knowledge_states")):
            if isinstance(state, dict):
                st.write(
                    f"{state.get('character_id')}｜知道：{', '.join(bt.as_list(state.get('knows')))}｜"
                    f"不知道：{', '.join(bt.as_list(state.get('does_not_know')))}"
                )

    st.subheader("可视化表达约束")
    st.caption("以下列出了小说信息中必须转化为可演、可见、可听表达的内容。这不是拍摄指导或镜头设计。")
    constraints = bt.filmic_constraints(screenplay)
    if constraints:
        for item in constraints:
            st.write(f"[{item.get('constraint_type')}] {item.get('summary')}")
            st.caption(bt.ref_text(item.get("source_refs", [])))
    else:
        st.info("暂无可视化表达约束。")

    st.subheader("伏笔追踪")
    foreshadowing = [item for item in bt.as_list(screenplay.get("foreshadowing")) if isinstance(item, dict)]
    if foreshadowing:
        for item in foreshadowing:
            st.write(f"{item.get('id')}｜{item.get('status')}｜{item.get('description')}")
    else:
        st.info("暂无伏笔追踪。")


def render(project: dict):
    """渲染生成结果页面——仅展示 YAML 结构预览。"""
    st.header("📋 生成结果")
    st.markdown("---")

    # ---- Fake Provider 检测 ----
    if _looks_like_fake_provider(project):
        st.warning(
            "当前为 Fake Provider 模式，内容为根据当前项目章节构造的模拟生成结果，"
            "不是真实 AI 创作。"
        )

    # ---- 获取 backend_project_id ----
    project_id = data_loader.get_backend_project_id(project)

    # ---- 从后端拉取最新的 screenplay_yaml / screenplay_json ----
    yaml_text = ""
    screenplay = data_loader.load_screenplay_data(project)
    if project_id:
        try:
            yaml_text = data_loader.load_screenplay_yaml(project)
        except Exception as exc:
            logger.warning("拉取 screenplay_yaml 失败: %s", exc)
            st.warning("无法从后端加载 YAML 数据，请确认后端服务已启动。")
    else:
        # 尝试从本地缓存读取
        yaml_text = project.get("screenplay_yaml") or ""

    # ---- 无数据提示 ----
    if not yaml_text:
        job_status = project.get("backend_job_status", "idle")
        if job_status == "succeeded":
            st.info("生成已完成，但暂无 YAML 结构数据。")
        elif job_status in ("queued", "running"):
            st.info("剧本正在生成中，请稍后再来查看。")
        else:
            st.info("还没有 YAML 结构数据，请先在「原文管理」页面导入原文并点击「开始生成结构化剧本」")
    else:
        yaml_tab, evidence_tab = st.tabs(["YAML 结构", "改编证据"])
        # ---- YAML 结构预览 ----
        with yaml_tab:
            st.subheader("YAML 结构预览")
            st.code(yaml_text, language="yaml")

            # ---- 操作按钮 ----
            col1, col2, col3 = st.columns(3)

            with col1:
                # YAML 下载按钮
                if project_id:
                    try:
                        file_data = api_client.download_yaml(project_id)
                        st.download_button(
                            label="下载 YAML",
                            data=file_data.content,
                            file_name=file_data.filename,
                            mime=file_data.media_type,
                            use_container_width=True,
                        )
                    except api_client.ApiClientError as exc:
                        st.warning(f"YAML 下载暂不可用：{exc.message}")
                else:
                    st.button("下载 YAML", disabled=True, use_container_width=True)

            with col2:
                # YAML 校验按钮
                if project_id:
                    if st.button(
                        "校验当前 YAML",
                        use_container_width=True,
                        disabled=not bool(yaml_text),
                    ):
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
                else:
                    st.button("校验当前 YAML", disabled=True, use_container_width=True)

            with col3:
                # Schema 下载按钮
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
                else:
                    st.button("下载 Schema", disabled=True, use_container_width=True)
        with evidence_tab:
            _render_evidence_tab(screenplay)

    # ---- 底部提示信息 ----
    st.markdown("---")
    st.info(
        "其他生成内容已拆分到以下页面：人物管理、场景管理、情节、文学剧本预览、审查报告。"
        "请通过左侧导航访问。"
    )

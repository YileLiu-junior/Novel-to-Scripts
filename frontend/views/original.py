"""
original.py
<<<<<<< HEAD
原文管理页面：支持手动输入/粘贴、上传 txt 文件、字数限制、提交占位。

核心状态管理：
- TEXT_AREA_KEY：绑定 st.text_area 的 session_state key，
  只能在 st.text_area 渲染前修改，渲染后禁止直接赋值。
- PENDING_TEXT_KEY：中转 key，用于在按钮回调中暂存需要更新的文本，
  然后通过 st.rerun() 触发页面重新运行，在 st.text_area 渲染前同步到 TEXT_AREA_KEY。
"""

import streamlit as st
from frontend.utils import storage

# ============ 常量 ============
MAX_TEXT_LENGTH = 20000       # 原文最大字数
MAX_FILE_SIZE = 100 * 1024    # 上传文件大小限制（100KB）
TEXT_AREA_KEY = "original_text_input"      # text_area 的 session_state key
PENDING_TEXT_KEY = "pending_original_text"  # 中转 key，用于 pending state 模式


def truncate_text(text: str, max_length: int = MAX_TEXT_LENGTH) -> str:
    """
    截断文本到指定最大长度。
    :param text: 原始文本
    :param max_length: 最大字数
    :return: 截断后的文本
    """
    if len(text) <= max_length:
        return text
    return text[:max_length]


def decode_txt_file(uploaded_file) -> str | None:
    """
    解码上传的 txt 文件内容。
    优先使用 UTF-8，失败后尝试 GBK。
    :param uploaded_file: st.file_uploader 返回的文件对象
    :return: 解码后的文本字符串；解码失败返回 None
    """
    raw_bytes = uploaded_file.read()
    # 优先 UTF-8
=======
原文管理与生成流程页面。

该页面遵循后端 V0+V1 contract：前端只上传并读取 txt 文本，再调用章节
导入或自动拆章接口；生成流程通过 job 轮询和 artifact 拉取完成。
"""

from __future__ import annotations

import re
import time
from typing import Any

import streamlit as st

from frontend import api_client
from frontend.utils import storage, state


MAX_FILE_SIZE = 10 * 1024 * 1024
STEP_LABELS = {
    "novel_reader": "小说解析中",
    "story_ontology": "故事圣经生成中",
    "adaptation_planner": "改编计划生成中",
    "screenplay_writer": "剧本写作中",
    "complete": "生成完成",
}


def decode_txt_file(uploaded_file) -> str | None:
    """解码 txt 文件，优先 UTF-8，兼容常见中文 GBK 编码。"""
    raw_bytes = uploaded_file.read()
>>>>>>> 7be98a4 (feat: add screenplay schema design and JSON/YAML definitions)
    try:
        return raw_bytes.decode("utf-8")
    except UnicodeDecodeError:
        pass
<<<<<<< HEAD
    # 回退 GBK
=======
>>>>>>> 7be98a4 (feat: add screenplay schema design and JSON/YAML definitions)
    try:
        return raw_bytes.decode("gbk")
    except UnicodeDecodeError:
        return None


<<<<<<< HEAD
def render(project: dict):
    """
    渲染原文管理页面。
    :param project: 当前项目字典
    """
    st.header("📄 原文管理")
    st.markdown("---")

    # ---- 说明文字 ----
    st.info(
        "💡 使用说明：\n"
        "1. 可直接在下方文本框中粘贴小说原文。\n"
        "2. 也可以上传 txt 文件，内容会自动填入文本框。\n"
        f"3. 当前最多保存 **{MAX_TEXT_LENGTH}** 字。\n"
        f"4. txt 文件大小不能超过 **{MAX_FILE_SIZE // 1024}KB**。**"
    )

    # ---- 初始化 session_state ----
    # 首次进入页面时，用项目已有原文初始化 TEXT_AREA_KEY
    if TEXT_AREA_KEY not in st.session_state:
        st.session_state[TEXT_AREA_KEY] = project.get("original_text", "")

    # ---- 处理 pending state（必须在 st.text_area 渲染之前）----
    # 如果存在 pending 文本，先同步到 TEXT_AREA_KEY，然后删除 pending
    if PENDING_TEXT_KEY in st.session_state:
        st.session_state[TEXT_AREA_KEY] = st.session_state[PENDING_TEXT_KEY]
        del st.session_state[PENDING_TEXT_KEY]

    # ---- 文件上传组件 ----
    uploaded_file = st.file_uploader("上传 txt 原文文件", type=["txt"], key="original_file_uploader")

    if uploaded_file is not None:
        # 检查文件大小
        file_size = uploaded_file.size
        if file_size > MAX_FILE_SIZE:
            st.error(f"文件过大（{file_size // 1024}KB），请上传不超过 {MAX_FILE_SIZE // 1024}KB 的 txt 文件。")
        else:
            # 读取并解码文件
            decoded_text = decode_txt_file(uploaded_file)
            if decoded_text is None:
                st.error("文件编码无法识别，请使用 UTF-8 或 GBK 编码的 txt 文件。")
            else:
                # 检查字数并截断
                original_len = len(decoded_text)
                decoded_text = truncate_text(decoded_text)
                # 通过 pending state 更新（避免在 file_uploader 后修改 TEXT_AREA_KEY）
                st.session_state[PENDING_TEXT_KEY] = decoded_text
                if original_len > MAX_TEXT_LENGTH:
                    st.warning(
                        f"文件内容超过 {MAX_TEXT_LENGTH} 字（共 {original_len} 字），"
                        f"已自动截取前 {MAX_TEXT_LENGTH} 字。"
                    )
                else:
                    st.success(f"文件读取成功，共 {original_len} 字，已填入文本框。")
                st.rerun()

    st.markdown("---")

    # ---- 文本编辑区 ----
    # 注意：使用 key 绑定 session_state，不要同时传 value（否则会冲突）
    text_input = st.text_area(
        "小说原文",
        height=500,
        placeholder="请在此输入或粘贴小说原文...",
        label_visibility="collapsed",
        key=TEXT_AREA_KEY,
    )

    # ---- 字数统计 ----
    current_len = len(text_input)
    if current_len > MAX_TEXT_LENGTH:
        st.warning(f"⚠️ 当前字数：**{current_len}** / {MAX_TEXT_LENGTH}（已超出，保存时将自动截取前 {MAX_TEXT_LENGTH} 字）")
    else:
        st.caption(f"当前字数：{current_len} / {MAX_TEXT_LENGTH}")

    # ---- 操作按钮区 ----
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 保存原文", use_container_width=True):
            # 截断到最大长度
            truncated = False
            save_text = text_input
            if len(save_text) > MAX_TEXT_LENGTH:
                save_text = truncate_text(save_text)
                truncated = True

            # 保存到项目数据
            project_id = project.get("id")
            updated = storage.update_project(project_id, {"original_text": save_text})
            if updated:
                # 通过 pending state 同步文本框内容（避免在 text_area 渲染后修改 TEXT_AREA_KEY）
                st.session_state[PENDING_TEXT_KEY] = save_text
                st.success("原文已保存。")
                if truncated:
                    st.warning(f"文本超过 {MAX_TEXT_LENGTH} 字，已自动截取前 {MAX_TEXT_LENGTH} 字后保存。")
                st.rerun()
            else:
                st.error("保存失败，请重试。")

    with col2:
        if st.button("🚀 提交", use_container_width=True):
            st.info("提交功能暂未实现，后续将用于触发小说解析与剧本生成。")
=======
def parse_chapter_markers(text: str) -> list[dict[str, str]]:
    """按常见章回标题把 txt 切成章节，供 PUT /chapters 使用。"""
    pattern = re.compile(r"(?m)^\s*((第[一二三四五六七八九十百千万\d]+[章节回卷].*)|(Chapter\s+\d+.*))\s*$")
    matches = list(pattern.finditer(text))
    if not matches:
        return [{"title": "全文", "text": text.strip()}] if text.strip() else []

    chapters: list[dict[str, str]] = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        title = match.group(1).strip()
        body = text[start:end].strip()
        chapters.append({"title": title, "text": body or title})
    return chapters


def ensure_backend_project(project: dict) -> str | None:
    """确保当前本地项目已映射到后端 project。"""
    backend_project_id = project.get("backend_project_id")
    if backend_project_id:
        return backend_project_id

    try:
        backend_project = api_client.create_project(
            title=project.get("name", "未命名项目"),
            logline=project.get("description") or None,
        )
    except api_client.ApiClientError as exc:
        st.error(exc.message)
        return None

    backend_project_id = backend_project.get("id")
    storage.update_project(project["id"], {"backend_project_id": backend_project_id})
    st.session_state.backend_project_id = backend_project_id
    return backend_project_id


def _sync_project_state(project_id: str, updates: dict[str, Any]) -> None:
    """同时更新本地项目文件和 session_state，保持刷新后可恢复。"""
    storage.update_project(project_id, updates)
    for key, value in updates.items():
        st.session_state[key] = value


def _refresh_chapters(project: dict, backend_project_id: str) -> list[dict[str, Any]]:
    try:
        chapters = api_client.list_chapters(backend_project_id)
        _sync_project_state(project["id"], {"backend_chapters": chapters})
        return chapters
    except api_client.ApiClientError as exc:
        st.warning(exc.message)
        return project.get("backend_chapters", []) or []


def _load_generation_artifacts(project: dict, backend_project_id: str) -> None:
    """生成成功后抓取主要 artifacts，供结果页六个 Tab 消费。"""
    updates: dict[str, Any] = {}
    try:
        updates["backend_artifacts"] = api_client.list_artifacts(backend_project_id)
    except api_client.ApiClientError:
        updates["backend_artifacts"] = []

    for artifact_type, key in (
        ("screenplay_json", "screenplay_data"),
        ("screenplay_yaml", "screenplay_yaml"),
        ("audit_report", "audit_report"),
        ("screenplay_rendered", "screenplay_rendered"),
    ):
        try:
            artifact = api_client.get_artifact(backend_project_id, artifact_type)
            updates[key] = artifact.get("data")
        except api_client.ApiClientError:
            updates.setdefault(key, {} if artifact_type != "screenplay_yaml" else "")

    try:
        rendered = api_client.get_rendered(backend_project_id, "markdown")
        updates["rendered_markdown"] = rendered.get("content", "")
    except api_client.ApiClientError:
        rendered_artifact = updates.get("screenplay_rendered")
        if isinstance(rendered_artifact, dict):
            updates["rendered_markdown"] = (
                rendered_artifact.get("formats", {}).get("markdown", {}).get("content", "")
            )

    _sync_project_state(project["id"], updates)


def _render_chapter_list(chapters: list[dict[str, Any]]) -> None:
    st.subheader(f"章节列表（共 {len(chapters)} 章）")
    if not chapters:
        st.info("尚未导入章节。")
        return

    for chapter in chapters:
        paragraphs = chapter.get("paragraphs", []) or []
        preview = ""
        if paragraphs:
            preview = paragraphs[0].get("text") or paragraphs[0].get("summary") or ""
        if not preview and chapter.get("text"):
            preview = chapter.get("text", "")[:100]
        preview = preview[:100]
        word_count = chapter.get("word_count")
        if word_count is None:
            word_count = len(chapter.get("text", "") or "")

        with st.container(border=True):
            st.markdown(f"**{chapter.get('order', '-')}. {chapter.get('title', '未命名章节')}**")
            st.caption(
                f"章节 ID：{chapter.get('id', '后端自动生成')} | "
                f"字数：{word_count} | 段落数：{len(paragraphs)}"
            )
            st.write(preview or "暂无预览")


def _render_generation_controls(project: dict, backend_project_id: str, chapters: list[dict[str, Any]]) -> None:
    st.subheader("改编参数与生成")
    col1, col2 = st.columns(2)
    with col1:
        target_format = st.selectbox(
            "目标格式",
            ["web_series", "short_drama", "film", "general"],
            index=0,
        )
        fidelity_level = st.selectbox("忠实度", ["low", "medium", "high"], index=2)
    with col2:
        dialogue_style = st.text_input("对白风格", value="restrained_with_subtext")
        priorities_text = st.text_input("保留重点", value="relationship_arc, foreshadowing")

    priorities = [item.strip() for item in priorities_text.split(",") if item.strip()]
    config = {
        "target_format": target_format,
        "fidelity_level": fidelity_level,
        "preserve_priorities": priorities,
        "dialogue_style": dialogue_style.strip() or "restrained_with_subtext",
    }

    if len(chapters) < 3:
        st.warning("至少需要导入 3 章后才能生成剧本。")

    if st.button("开始生成结构化剧本", use_container_width=True, disabled=len(chapters) < 3):
        try:
            response = api_client.generate_screenplay(backend_project_id, config)
        except api_client.ApiClientError as exc:
            st.error(exc.message)
            return
        _sync_project_state(
            project["id"],
            {
                "backend_job_id": response.get("job_id"),
                "backend_job_status": response.get("status", "queued"),
                "backend_current_step": "novel_reader",
                "backend_error": None,
            },
        )
        st.rerun()

    job_id = project.get("backend_job_id") or st.session_state.get("backend_job_id")
    if not job_id:
        return

    try:
        job = api_client.get_job(job_id)
    except api_client.ApiClientError as exc:
        st.error(exc.message)
        return

    status_value = job.get("status", "idle")
    current_step = job.get("current_step")
    error_value = job.get("error")
    _sync_project_state(
        project["id"],
        {
            "backend_job_status": status_value,
            "backend_current_step": current_step,
            "backend_error": error_value,
        },
    )

    label = STEP_LABELS.get(current_step or "", "排队中" if status_value == "queued" else status_value)
    if status_value in ("queued", "running"):
        st.info(f"生成中：{label}")
        st.progress(0.25 if status_value == "queued" else 0.65)
        time.sleep(1.6)
        st.rerun()
    elif status_value == "failed":
        formatted_error = _format_job_error(error_value)
        st.error(f"生成失败：\n\n{formatted_error}")
        if st.button("重试生成", use_container_width=True):
            _sync_project_state(project["id"], {"backend_job_id": None, "backend_job_status": "idle"})
            st.rerun()
    elif status_value == "succeeded":
        st.success("生成完成，正在准备结果页。")
        _load_generation_artifacts(project, backend_project_id)
        state.switch_section("export")


def _format_job_error(error_value: str | None) -> str:
    """把后端 schema 错误中的 path/schema_path 拆成前端易读文本。"""
    if not error_value:
        return "后端未返回具体错误。"
    parts = [part.strip() for part in error_value.split(";")]
    lines = [parts[0]]
    for part in parts[1:]:
        if part.startswith("path="):
            lines.append(f"字段路径：{part.removeprefix('path=')}")
        elif part.startswith("schema_path="):
            lines.append(f"Schema 路径：{part.removeprefix('schema_path=')}")
        else:
            lines.append(part)
    return "\n".join(lines)


def render(project: dict):
    """渲染原文管理、章节导入和生成流程。"""
    st.header("原文管理")
    st.caption("选择 txt 文件后，前端读取文本内容，再调用后端章节接口。")
    st.markdown("---")

    backend_project_id = ensure_backend_project(project)
    if not backend_project_id:
        st.info(f"后端 Base URL：{api_client.get_base_url()}")
        return

    st.caption(f"后端项目 ID：`{backend_project_id}` | Base URL：`{api_client.get_base_url()}`")

    import_mode = st.radio(
        "导入方式",
        ["自动拆章", "按章节标记导入"],
        horizontal=True,
        help="自动拆章调用后端 auto-split；按章节标记导入由前端按章标题切分后调用 PUT chapters。",
    )
    uploaded_file = st.file_uploader("上传 txt 原文文件（不超过 10MB）", type=["txt"])

    if uploaded_file is not None:
        if uploaded_file.size > MAX_FILE_SIZE:
            st.error("文件过大，请上传 10MB 以内的 txt 文件。")
        else:
            text = decode_txt_file(uploaded_file)
            if text is None:
                st.error("文件编码无法识别，请使用 UTF-8 或 GBK 编码。")
            elif st.button("导入章节", use_container_width=True):
                try:
                    if import_mode == "自动拆章":
                        split_response = api_client.auto_split_chapters(backend_project_id, text, "auto")
                        st.success(f"自动拆章完成，共 {split_response.get('chapter_count', 0)} 章。")
                    else:
                        chapters_to_save = parse_chapter_markers(text)
                        api_client.replace_chapters(backend_project_id, chapters_to_save)
                        st.success(f"章节导入完成，共 {len(chapters_to_save)} 章。")
                    _refresh_chapters(project, backend_project_id)
                    st.rerun()
                except api_client.ApiClientError as exc:
                    st.error(exc.message)

    st.markdown("---")
    chapters = _refresh_chapters(project, backend_project_id)
    _render_chapter_list(chapters)

    st.markdown("---")
    _render_generation_controls(project, backend_project_id, chapters)
>>>>>>> 7be98a4 (feat: add screenplay schema design and JSON/YAML definitions)

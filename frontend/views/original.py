"""
original.py
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
    try:
        return raw_bytes.decode("utf-8")
    except UnicodeDecodeError:
        pass
    # 回退 GBK
    try:
        return raw_bytes.decode("gbk")
    except UnicodeDecodeError:
        return None


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

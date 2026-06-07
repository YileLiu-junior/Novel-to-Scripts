"""
theme.py
侘寂文艺主题 —— 深色底+暖纸色，老式打字机稿纸质感。

通过 CSS 注入到 Streamlit 应用，不修改任何 UX 交互逻辑和 API 接口。
"""

from __future__ import annotations

import streamlit as st

# ── 色板（OKLCH 色域）────────────────────────────────────────────
INK = "#2b2318"         # 稿纸墨色 — 标题、正文
WARM_CREAM = "#f0e6d3"  # 暖纸底 — 浅色表面
PARCHMENT = "#e8dcc8"   # 旧纸 — 稍深暖纸
RUST = "#b85c3c"        # 锈红 — 唯一强调色
PATINA = "#7a8b6a"      # 铜绿 — 辅助色
DARK_BASE = "#1c1814"   # 深底 — 主背景
DARK_SIDEBAR = "#151210" # 更深侧栏
DARK_SURFACE = "#231f1a" # 卡片/容器暗底
TEXT_ON_DARK = "#e4d5bf" # 暗底文字
TEXT_MUTED = "#9b8c78"   # 弱化文字
BORDER_WARM = "rgba(184, 92, 60, 0.12)"  # 暖色边框
BORDER_PAPER = "rgba(43, 35, 24, 0.08)"  # 纸面边框


def _css() -> str:
    """生成完整的侘寂主题 CSS。"""
    return f"""
    /* ══════════════════════════════════════════════════════════
       侘寂 · 打字机稿纸主题
       Wabi-sabi Typewriter Manuscript Theme
       ══════════════════════════════════════════════════════════ */

    /* ── 根：深底 + 噪点纹理 ─────────────────────────────── */
    .stApp {{
        background-color: {DARK_BASE};
        background-image:
            url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.03'/%3E%3C/svg%3E");
    }}

    /* ── 主内容区：暖纸底卡片 ─────────────────────────────── */
    .main .block-container {{
        padding-top: 2rem;
        padding-bottom: 4rem;
    }}

    /* ── 标题：衬线体 ─────────────────────────────────────── */
    h1 {{
        font-family: 'Georgia', 'Noto Serif SC', 'Source Han Serif SC', 'SimSun', serif !important;
        color: {TEXT_ON_DARK} !important;
        font-weight: 400 !important;
        letter-spacing: 0.04em !important;
        border-bottom: 1px solid {BORDER_WARM};
        padding-bottom: 0.6em;
        margin-bottom: 0.8em;
    }}

    h2 {{
        font-family: 'Georgia', 'Noto Serif SC', 'Source Han Serif SC', serif !important;
        color: {TEXT_ON_DARK} !important;
        font-weight: 400 !important;
        letter-spacing: 0.03em !important;
    }}

    h3, h4 {{
        font-family: 'Georgia', 'Noto Serif SC', serif !important;
        color: {TEXT_ON_DARK} !important;
        font-weight: 400 !important;
    }}

    /* ── 正文 ──────────────────────────────────────────────── */
    p, li, label, .stMarkdown {{
        color: {TEXT_ON_DARK} !important;
        line-height: 1.75 !important;
    }}

    .stCaption {{
        color: {TEXT_MUTED} !important;
        font-size: 0.82rem !important;
    }}

    /* ── 侧栏：更深底 + 格纹纸底部 ────────────────────────── */
    [data-testid="stSidebar"] {{
        background-color: {DARK_SIDEBAR};
        background-image:
            repeating-linear-gradient(
                0deg,
                transparent,
                transparent 28px,
                rgba(184, 92, 60, 0.04) 28px,
                rgba(184, 92, 60, 0.04) 29px
            );
    }}

    [data-testid="stSidebar"] h2 {{
        color: {TEXT_ON_DARK} !important;
        font-family: 'Georgia', serif !important;
        font-size: 1.1rem !important;
        letter-spacing: 0.06em !important;
    }}

    [data-testid="stSidebar"] .stButton button {{
        background: transparent !important;
        border: 1px solid {BORDER_WARM} !important;
        color: {TEXT_ON_DARK} !important;
        font-size: 0.88rem !important;
        border-radius: 2px !important;
        transition: background 0.25s ease !important;
    }}

    [data-testid="stSidebar"] .stButton button:hover {{
        background: rgba(184, 92, 60, 0.08) !important;
        border-color: rgba(184, 92, 60, 0.35) !important;
    }}

    /* ── 按钮：锈红强调 ───────────────────────────────────── */
    .stButton button {{
        background: transparent !important;
        border: 1px solid rgba(184, 92, 60, 0.25) !important;
        color: {TEXT_ON_DARK} !important;
        border-radius: 2px !important;
        font-size: 0.9rem !important;
        letter-spacing: 0.02em !important;
        transition: background 0.25s ease, border-color 0.25s ease !important;
    }}

    .stButton button:hover {{
        background: rgba(184, 92, 60, 0.1) !important;
        border-color: {RUST} !important;
        color: #f0c4a8 !important;
    }}

    .stButton button:active {{
        background: rgba(184, 92, 60, 0.18) !important;
    }}

    /* 主操作按钮（type=primary）*/
    .stButton button[kind="primary"] {{
        background: rgba(184, 92, 60, 0.15) !important;
        border-color: {RUST} !important;
    }}

    .stButton button[kind="primary"]:hover {{
        background: rgba(184, 92, 60, 0.28) !important;
    }}

    /* ── 卡片容器：稿纸质感 ───────────────────────────────── */
    [data-testid="stVerticalBlockBorderWrapper"],
    .stContainer {{
        background-color: {DARK_SURFACE} !important;
        border: 1px solid {BORDER_WARM} !important;
        border-radius: 2px !important;
        padding: 1.25rem !important;
        /* 稿纸底部格线 */
        background-image:
            repeating-linear-gradient(
                0deg,
                transparent,
                transparent 26px,
                rgba(184, 92, 60, 0.06) 26px,
                rgba(184, 92, 60, 0.06) 27px
            ) !important;
    }}

    /* ── 输入框 & 文本域：暖纸墨色 ─────────────────────────── */
    .stTextInput input,
    .stTextArea textarea,
    .stSelectbox [data-baseweb="select"] > div,
    .stNumberInput input {{
        background-color: rgba(240, 230, 211, 0.05) !important;
        border: 1px solid {BORDER_WARM} !important;
        color: {TEXT_ON_DARK} !important;
        border-radius: 2px !important;
        font-family: 'Georgia', 'Noto Serif SC', serif !important;
        font-size: 0.92rem !important;
    }}

    .stTextInput input:focus,
    .stTextArea textarea:focus {{
        border-color: {RUST} !important;
        box-shadow: 0 0 0 1px rgba(184, 92, 60, 0.2) !important;
        background-color: rgba(240, 230, 211, 0.08) !important;
    }}

    .stTextInput input::placeholder,
    .stTextArea textarea::placeholder {{
        color: {TEXT_MUTED} !important;
        font-style: italic !important;
    }}

    /* ── Radio / Checkbox ──────────────────────────────────── */
    .stRadio label, .stCheckbox label {{
        color: {TEXT_ON_DARK} !important;
    }}

    /* ── 分隔线 ────────────────────────────────────────────── */
    hr {{
        border-color: {BORDER_WARM} !important;
        margin: 1.5rem 0 !important;
    }}

    /* ── 代码块：打字机风格 ────────────────────────────────── */
    code {{
        font-family: 'Courier New', 'Source Code Pro', monospace !important;
        background-color: rgba(240, 230, 211, 0.06) !important;
        color: {PARCHMENT} !important;
        border-radius: 2px !important;
        padding: 0.15em 0.4em !important;
        font-size: 0.88rem !important;
    }}

    pre {{
        background-color: {DARK_SIDEBAR} !important;
        border: 1px solid {BORDER_WARM} !important;
        border-radius: 2px !important;
        padding: 1.25rem !important;
        font-family: 'Courier New', 'Source Code Pro', monospace !important;
        /* 打字机纸格线 */
        background-image:
            repeating-linear-gradient(
                0deg,
                transparent,
                transparent 22px,
                rgba(184, 92, 60, 0.05) 22px,
                rgba(184, 92, 60, 0.05) 23px
            ) !important;
    }}

    pre code {{
        background: transparent !important;
        padding: 0 !important;
    }}

    /* ── 表格 / DataFrame ──────────────────────────────────── */
    .stDataFrame {{
        border: 1px solid {BORDER_WARM} !important;
        border-radius: 2px !important;
    }}

    /* ── Expander ──────────────────────────────────────────── */
    .stExpander {{
        border: 1px solid {BORDER_WARM} !important;
        border-radius: 2px !important;
        background: {DARK_SURFACE} !important;
    }}

    /* ── 信息 / 警告 / 错误提示 ────────────────────────────── */
    .stAlert {{
        border-radius: 2px !important;
        border-left: 2px solid {RUST} !important;
        background-color: rgba(184, 92, 60, 0.06) !important;
    }}

    [data-testid="stInfo"] {{
        border-left-color: {PATINA} !important;
        background-color: rgba(122, 139, 106, 0.06) !important;
    }}

    [data-testid="stSuccess"] {{
        border-left-color: #6b8b5e !important;
        background-color: rgba(107, 139, 94, 0.08) !important;
    }}

    [data-testid="stWarning"] {{
        border-left-color: #c4956a !important;
        background-color: rgba(196, 149, 106, 0.08) !important;
    }}

    [data-testid="stError"] {{
        border-left-color: {RUST} !important;
        background-color: rgba(184, 92, 60, 0.1) !important;
    }}

    /* ── Progress Bar ──────────────────────────────────────── */
    .stProgress > div > div {{
        background-color: {RUST} !important;
    }}

    /* ── Tabs ──────────────────────────────────────────────── */
    .stTabs [data-baseweb="tab"] {{
        color: {TEXT_MUTED} !important;
        font-family: 'Georgia', serif !important;
    }}

    .stTabs [aria-selected="true"] {{
        color: {RUST} !important;
        border-bottom-color: {RUST} !important;
    }}

    /* ── File Uploader ─────────────────────────────────────── */
    [data-testid="stFileUploader"] {{
        border: 1px dashed {BORDER_WARM} !important;
        border-radius: 2px !important;
        background-color: rgba(240, 230, 211, 0.02) !important;
    }}

    /* ── 表单 submit button ────────────────────────────────── */
    .stFormSubmitButton button {{
        background: rgba(184, 92, 60, 0.12) !important;
        border-color: {RUST} !important;
        color: {TEXT_ON_DARK} !important;
    }}

    .stFormSubmitButton button:hover {{
        background: rgba(184, 92, 60, 0.25) !important;
    }}

    /* ── 滚动条 ────────────────────────────────────────────── */
    ::-webkit-scrollbar {{
        width: 6px;
    }}

    ::-webkit-scrollbar-track {{
        background: {DARK_BASE};
    }}

    ::-webkit-scrollbar-thumb {{
        background: rgba(184, 92, 60, 0.25);
        border-radius: 3px;
    }}

    ::-webkit-scrollbar-thumb:hover {{
        background: rgba(184, 92, 60, 0.45);
    }}

    /* ── 选中文字高亮 ──────────────────────────────────────── */
    ::selection {{
        background: rgba(184, 92, 60, 0.35);
        color: #f0e6d3;
    }}

    /* ── Tooltip ───────────────────────────────────────────── */
    .stTooltipContent {{
        background: {DARK_SIDEBAR} !important;
        border: 1px solid {BORDER_WARM} !important;
        color: {TEXT_ON_DARK} !important;
    }}
    """


def inject() -> None:
    """注入侘寂文艺主题 CSS。在 app.py 的 set_page_config 之后调用一次即可。"""
    st.markdown(f"<style>{_css()}</style>", unsafe_allow_html=True)

"""Deterministic screenplay renderer — 将 screenplay_json 投影为可读文学剧本文本。

不做 AI 重写，不改 schema，仅从 scenes[].content_blocks 和 dialogue 中
提取已存在的文字拼成 Markdown 或纯文本。

规则：
- 默认不输出 subtext / surface_intent / emotional_state（保持预览干净）。
- 对白行格式：**角色名** + action_hint（括号内）+ 台词正文。
"""

from __future__ import annotations

from typing import Any


class ScreenplayRenderExporter:
    """把 screenplay_json 渲染为 Markdown 或纯文本。"""

    MARKDOWN_MEDIA_TYPE = "text/markdown; charset=utf-8"
    TEXT_MEDIA_TYPE = "text/plain; charset=utf-8"

    # ------------------------------------------------------------------
    # 公共入口
    # ------------------------------------------------------------------

    def render_markdown(self, screenplay: dict[str, Any]) -> str:
        """渲染 Markdown 格式的文学剧本。"""
        return self._render(screenplay, format_="markdown")

    def render_text(self, screenplay: dict[str, Any]) -> str:
        """渲染纯文本格式的文学剧本。"""
        return self._render(screenplay, format_="text")

    # ------------------------------------------------------------------
    # 渲染引擎
    # ------------------------------------------------------------------

    def _render(self, screenplay: dict[str, Any], *, format_: str) -> str:
        """核心渲染逻辑。"""
        project = screenplay.get("project", {})
        source = screenplay.get("source", {})
        title = project.get("title", "未命名剧本")
        logline = project.get("logline", "")

        # 构建角色 ID → 名称映射
        char_names = self._build_char_name_map(screenplay)

        lines: list[str] = []
        md = format_ == "markdown"

        # 标题
        lines.append(f"# {title}" if md else title)
        if logline:
            lines.append(f"> {logline}" if md else logline)
        lines.append("")

        # 源信息
        chapters = source.get("chapters", [])
        if chapters:
            chapter_str = "、".join(ch.get("title", ch.get("id", "")) for ch in chapters)
            lines.append(f"**原著**: {chapter_str}" if md else f"原著: {chapter_str}")
            lines.append("")

        # 遍历每场戏
        scenes = screenplay.get("scenes", [])
        for scene_index, scene in enumerate(scenes, start=1):
            if not isinstance(scene, dict):
                continue

            # 场景标题
            heading = scene.get("scene_heading", {})
            heading_text = heading.get("text", f"{scene_index}. 未命名场景")
            if md:
                lines.append(f"## {heading_index(heading_text, scene_index)}")
            else:
                lines.append(heading_text)
            lines.append("")

            # content_blocks 按顺序渲染
            blocks = scene.get("content_blocks", [])
            for block in blocks:
                if not isinstance(block, dict):
                    continue
                block_type = block.get("block_type", "action")
                text = block.get("text", "").strip()
                if not text:
                    continue

                if block_type == "dialogue":
                    # 新 prompt 下 content_blocks.text 已包含完整中文剧本格式：
                    # "角色名：（动作提示）台词正文"
                    # 直接输出即可，无需二次拼装
                    if md:
                        # 对 dialogue block 做角色名加粗
                        char_id = block.get("character_id", "")
                        char_name = char_names.get(char_id, "")
                        if char_name and text.startswith(char_name):
                            # 分离角色名和后续内容
                            rest = text[len(char_name):]
                            lines.append(f"**{char_name}**{rest}")
                        else:
                            lines.append(text)
                    else:
                        lines.append(text)
                else:
                    # action — 以中文剧本惯例的 △ 前缀输出
                    action_text = text if text.startswith("△") else f"△{text}"
                    lines.append(action_text)

                lines.append("")

            # 场与场之间额外空行
            lines.append("")

        return "\n".join(lines).strip() + "\n"

    # ------------------------------------------------------------------
    # 辅助方法
    # ------------------------------------------------------------------

    @staticmethod
    def _build_char_name_map(screenplay: dict[str, Any]) -> dict[str, str]:
        """从 story_bible.characters 构建 id → name 映射。"""
        name_map: dict[str, str] = {}
        bible = screenplay.get("story_bible", {})
        for char in bible.get("characters", []):
            if isinstance(char, dict):
                char_id = char.get("id", "")
                char_name = char.get("name", "")
                if char_id and char_name:
                    name_map[char_id] = char_name
        return name_map

def heading_index(heading_text: str, fallback: int) -> str:
    """从 scene heading 中提取序号前缀，保持为 Markdown heading 文本。"""
    # 如果 heading 已经以数字开头，直接用
    stripped = heading_text.strip()
    if stripped and stripped[0].isdigit():
        return stripped
    # 否则补充序号
    return f"{fallback}. {stripped}"

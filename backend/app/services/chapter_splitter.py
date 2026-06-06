"""章节拆分服务：将用户输入的原始文本按章节标记自动切分为章节列表。

支持两种模式：
- rule: 纯正则匹配，速度快，适合有明确章节标记的文本
- auto: 先尝试正则，若未检测到标记则交给 LLM 切分
"""

from __future__ import annotations

import re
from typing import Any


# ---------------------------------------------------------------------------
# 章节标记正则
# ---------------------------------------------------------------------------

_CHAPTER_PATTERNS: list[tuple[str, int]] = [
    # 中文章回体：第X章 / 第X节 / 第X回 / 第X卷
    (r"^第[零一二三四五六七八九十百千万\d]+[章节回卷部集]", 1),
    # 中文简写：第一章 / 一、
    (r"^[零一二三四五六七八九十百千万]+[、，。．\s]", 1),
    # 英文：Chapter X / CHAPTER X
    (r"^\s*Chapter\s+[\dIVXivx]+", 1),
    (r"^\s*CHAPTER\s+[\dIVXivx]+", 1),
    # 英文：Part X / Book X
    (r"^\s*Part\s+[\dIVXivx]+", 1),
    (r"^\s*Book\s+[\dIVXivx]+", 1),
    # 纯数字序号：1. / 1、/ 1．
    (r"^\s*\d+[\.、．]\s*\S", 1),
]

# 编译正则
_COMPILED_PATTERNS = [(re.compile(pattern, re.MULTILINE), priority) for pattern, priority in _CHAPTER_PATTERNS]

# ---------------------------------------------------------------------------
# 切分结果
# ---------------------------------------------------------------------------

class SplitChapter:
    """拆分后的章节数据，在持久化前使用。"""

    def __init__(self, title: str, text: str, order: int) -> None:
        self.title = title
        self.text = text
        self.order = order

    def to_dict(self) -> dict[str, Any]:
        return {"title": self.title, "text": self.text, "order": self.order}


# ---------------------------------------------------------------------------
# ChapterSplitter
# ---------------------------------------------------------------------------

class ChapterSplitter:
    """原始文本 → 章节列表 的拆分器。"""

    def __init__(self, ai_provider: Any | None = None) -> None:
        self.ai_provider = ai_provider

    # ------------------------------------------------------------------
    # 公共方法
    # ------------------------------------------------------------------

    def split(self, raw_text: str, mode: str = "auto") -> list[SplitChapter]:
        """将 raw_text 拆分为章节。

        Args:
            raw_text: 用户输入的原始全文。
            mode: "rule"（仅正则）, "ai"（仅 LLM）, "auto"（先规则后 LLM）。

        Returns:
            SplitChapter 列表，含 title / text / order。
        """
        if not raw_text or not raw_text.strip():
            return []

        cleaned = self._normalize_text(raw_text)

        if mode == "rule":
            return self._split_by_rules(cleaned)
        if mode == "ai":
            return self._split_by_ai(cleaned)
        # auto: 先尝试规则
        rule_result = self._split_by_rules(cleaned)
        if len(rule_result) >= 2:
            return rule_result
        return self._split_by_ai(cleaned)

    # ------------------------------------------------------------------
    # 文本预处理
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_text(text: str) -> str:
        """统一换行符，去掉首尾空白。"""
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        # 去掉开头的空白行
        text = text.lstrip("\n")
        return text.strip()

    # ------------------------------------------------------------------
    # 规则切分
    # ------------------------------------------------------------------

    def _split_by_rules(self, text: str) -> list[SplitChapter]:
        """用正则检测章节边界并切分。"""
        boundaries = self._find_boundaries(text)
        if len(boundaries) < 2:
            return self._single_chapter(text)
        return self._slice_by_boundaries(text, boundaries)

    def _find_boundaries(self, text: str) -> list[int]:
        """找到所有章节起始位置（字符偏移量）。"""
        positions: set[int] = set()
        lines = text.split("\n")

        char_offset = 0
        for line in lines:
            for compiled, _priority in _COMPILED_PATTERNS:
                if compiled.match(line):
                    positions.add(char_offset)
                    break
            char_offset += len(line) + 1  # +1 for \n

        # 总是从文本开头开始
        positions.add(0)
        return sorted(positions)

    def _slice_by_boundaries(self, text: str, boundaries: list[int]) -> list[SplitChapter]:
        """按边界位置切出章节。"""
        chapters: list[SplitChapter] = []
        for i, start in enumerate(boundaries):
            end = boundaries[i + 1] if i + 1 < len(boundaries) else len(text)
            chunk = text[start:end].strip()
            if not chunk:
                continue
            title = self._extract_title(chunk)
            chapters.append(SplitChapter(title=title, text=chunk, order=len(chapters) + 1))
        return chapters

    @staticmethod
    def _extract_title(chunk: str) -> str:
        """从章节块首行提取标题。"""
        first_line = chunk.split("\n", 1)[0].strip()
        # 去掉首行中的 Markdown 标题标记
        first_line = re.sub(r"^#+\s*", "", first_line)
        # 截断过长标题
        if len(first_line) > 80:
            first_line = first_line[:77] + "..."
        return first_line or "未命名章节"

    @staticmethod
    def _single_chapter(text: str) -> list[SplitChapter]:
        """无章节标记时，将全文作为单独一章。"""
        title = ChapterSplitter._extract_title(text)
        return [SplitChapter(title=title, text=text, order=1)]

    # ------------------------------------------------------------------
    # AI 切分（占位）
    # ------------------------------------------------------------------

    def _split_by_ai(self, text: str) -> list[SplitChapter]:
        """用 LLM 检测章节边界并切分。

        当前占位实现：若规则切分结果不足，回退为单章处理。
        后续可接入 NovelReaderSkill 或其他轻量 skill 做语义切分。
        """
        # 如果文本很长但规则没找到标记，尝试用空行粗切
        paragraphs = text.split("\n\n")
        if len(paragraphs) >= 3:
            # 用空行分段作为最简切分
            mid = len(paragraphs) // 2
            chunk1 = "\n\n".join(paragraphs[:mid]).strip()
            chunk2 = "\n\n".join(paragraphs[mid:]).strip()
            if chunk1 and chunk2:
                return [
                    SplitChapter(title=self._extract_title(chunk1), text=chunk1, order=1),
                    SplitChapter(title=self._extract_title(chunk2), text=chunk2, order=2),
                ]
        return self._single_chapter(text)

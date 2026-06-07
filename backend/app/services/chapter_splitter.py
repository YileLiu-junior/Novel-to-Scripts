"""章节拆分服务：将用户输入的原始文本按章节标记自动切分为章节列表。

支持两种模式：
- rule: 纯正则匹配，速度快，适合有明确章节标记的文本
- auto: 先尝试正则，若无法得到 3 个可信正文章节，则交给轻量 AI boundary reader
"""

from __future__ import annotations

import re
from typing import Any


# ---------------------------------------------------------------------------
# 章节标记正则
# ---------------------------------------------------------------------------

_CHAPTER_PATTERNS: list[tuple[str, int]] = [
    # ── Markdown 标题行：###第X章 / ###楔子 / ###序幕 等 ──
    (r"^\s*#{1,3}\s*第[零一二三四五六七八九十百千万\d]+[章节回卷部集部分]", 1),
    (r"^\s*#{1,3}\s*楔[子文]", 1),
    (r"^\s*#{1,3}\s*序\s*[章言幕]", 1),
    (r"^\s*#{1,3}\s*引[子言文]", 1),
    (r"^\s*#{1,3}\s*前[传序言][\s（(]*[零一二三四五六七八九十百千万\d]*", 1),
    # ── 中文章回体：第X章 / 第X节 / 第X回 / 第X卷 / 第X部分 ──
    (r"^\s*第[零一二三四五六七八九十百千万\d]+[章节回卷部集部分]", 1),
    # ── 非标题行楔子/序幕/序章/引子/前传（无 ### 前缀）──
    (r"^\s*楔[子文]", 1),
    (r"^\s*序\s*[章言幕]", 1),
    (r"^\s*引[子言文]", 1),
    (r"^\s*前[传序言][\s（(]*[零一二三四五六七八九十百千万\d]*", 1),
    # 中文简写：第一章 / 一、
    (r"^\s*[零一二三四五六七八九十百千万]+[、，。．\s]", 1),
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
_MAIN_CHAPTER_HEADING_RE = re.compile(r"^\s*第(?P<number>[零一二三四五六七八九十百千万\d]+)章(?P<tail>.*)$")
_SECTION_TAIL_RE = re.compile(r"^\s*(?:[（(]\d+[）)]|第?\d+节|[零一二三四五六七八九十百千万\d]+)?\s*$")
_MIN_CHAPTER_BODY_CHARS = 80

_NON_STORY_HINTS = (
    "声明",
    "版权",
    "仅供预览",
    "请支持正版",
    "txt02.com",
    "本站",
    "下载",
    "手机阅读",
)

_CATALOG_TITLES = ("目录", "目 录", "contents", "content")
_PROLOGUE_TITLES = ("序章", "序", "楔子", "前言", "引子", "前传")

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


class SplitWarning:
    """章节拆分 warning，用于 artifact trace，不改变前端响应契约。"""

    def __init__(self, code: str, message: str, target: str | None = None) -> None:
        self.code = code
        self.message = message
        self.target = target

    def to_dict(self) -> dict[str, Any]:
        return {"code": self.code, "message": self.message, "target": self.target}


class IgnoredSpan:
    """被识别为声明、目录、广告或序章的 raw txt 行范围。"""

    def __init__(self, kind: str, start_line: int, end_line: int, reason: str) -> None:
        self.kind = kind
        self.start_line = start_line
        self.end_line = end_line
        self.reason = reason

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "reason": self.reason,
        }


class SplitResult:
    """ChapterSplitter 的内部结果，保留 trace；API 仍只返回 chapters/count/mode。"""

    def __init__(
        self,
        chapters: list[SplitChapter],
        mode_used: str,
        ignored_spans: list[IgnoredSpan] | None = None,
        warnings: list[SplitWarning] | None = None,
        ai_plan: dict[str, Any] | None = None,
    ) -> None:
        self.chapters = chapters
        self.mode_used = mode_used
        self.ignored_spans = ignored_spans or []
        self.warnings = warnings or []
        self.ai_plan = ai_plan

    def trace(self) -> dict[str, Any]:
        return {
            "mode_used": self.mode_used,
            "ignored_spans": [span.to_dict() for span in self.ignored_spans],
            "warnings": [warning.to_dict() for warning in self.warnings],
            "ai_plan": self.ai_plan,
        }


# ---------------------------------------------------------------------------
# ChapterSplitter
# ---------------------------------------------------------------------------

class ChapterSplitter:
    """原始文本 → 章节列表 的拆分器。"""

    def __init__(self, ai_provider: Any | None = None, boundary_reader: Any | None = None) -> None:
        self.ai_provider = ai_provider
        self.boundary_reader = boundary_reader

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
        return self.split_with_trace(raw_text, mode).chapters

    def split_with_trace(self, raw_text: str, mode: str = "auto") -> SplitResult:
        """拆分 raw_text，并保留 ignored spans、warnings 和 AI plan trace。"""
        if not raw_text or not raw_text.strip():
            return SplitResult([], mode_used=mode)

        cleaned = self._normalize_text(raw_text)

        if mode == "rule":
            return self._split_by_rules_with_trace(cleaned)
        if mode == "ai":
            return self._split_by_ai_with_trace(cleaned)
        rule_result = self._split_by_rules_with_trace(cleaned)
        if len(rule_result.chapters) >= 3:
            return rule_result
        ai_result = self._split_by_ai_with_trace(cleaned)
        return ai_result if ai_result.chapters else rule_result

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
        return self._split_by_rules_with_trace(text).chapters

    def _split_by_rules_with_trace(self, text: str) -> SplitResult:
        """用规则拆分正文主章节，并记录被忽略的非正文块。"""
        boundaries = self._find_boundaries(text)
        if len(boundaries) < 2:
            return SplitResult(
                self._single_chapter(text),
                mode_used="rule",
                warnings=[SplitWarning("chapters.too_few_after_rule_split", "规则拆分后可信正文少于 3 章")],
            )

        chapters: list[SplitChapter] = []
        ignored: list[IgnoredSpan] = []
        warnings: list[SplitWarning] = []
        for start, end in self._merge_same_chapter_boundaries(text, boundaries):
            chunk = text[start:end].strip()
            if not chunk:
                continue
            kind = self._classify_chunk(chunk)
            if kind != "main_chapter":
                start_line, end_line = self._line_range_for_offsets(text, start, end)
                ignored.append(IgnoredSpan(kind, start_line, end_line, "不计入正文前三章"))
                continue
            title = self._display_title(chunk)
            chapters.append(SplitChapter(title=title, text=chunk, order=len(chapters) + 1))
            warnings.extend(self._chapter_quality_warnings(title, chunk))
            if self._same_main_chapter_heading_count(chunk) > 1:
                warnings.append(
                    SplitWarning(
                        "chapter.boundary_suspicious",
                        "检测到同一章号下的多个内部小节标题，已合并为一个正文大章。",
                        title,
                    )
                )
            if len(chapters) == 3:
                break

        if len(chapters) < 3:
            warnings.append(SplitWarning("chapters.too_few_after_rule_split", "规则拆分后可信正文少于 3 章"))
        return SplitResult(chapters, mode_used="rule", ignored_spans=ignored, warnings=warnings)

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

    def _merge_same_chapter_boundaries(self, text: str, boundaries: list[int]) -> list[tuple[int, int]]:
        """把同一“第X章”下的分节边界合并，避免把（1）/第1节保存成空壳章节。"""
        merged: list[tuple[int, int]] = []
        current_start: int | None = None
        current_end: int | None = None
        current_key: str | None = None

        for i, start in enumerate(boundaries):
            end = boundaries[i + 1] if i + 1 < len(boundaries) else len(text)
            chunk = text[start:end].strip()
            title = self._extract_title(chunk) if chunk else ""
            key = self._main_chapter_number_key(title)

            if current_start is not None and key and current_key == key:
                current_end = end
                continue

            if current_start is not None and current_end is not None:
                merged.append((current_start, current_end))
            current_start = start
            current_end = end
            current_key = key

        if current_start is not None and current_end is not None:
            merged.append((current_start, current_end))
        return merged

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

    def _classify_chunk(self, chunk: str) -> str:
        """判断切片是否是正文主章节，还是声明、目录等非正文。

        楔子/序幕/序章/引子 不再被排除——很多小说（如《潜伏》）以楔子或序章
        作为正文起点，这些内容对 NovelReader 有实际价值。
        """
        title = self._extract_title(chunk)
        first_line = title.lower()
        compact = re.sub(r"\s+", "", chunk.lower())
        if self._has_notice_hint_near_start(chunk, compact):
            return "ignored_notice"
        if any(first_line == item.lower() for item in _CATALOG_TITLES):
            return "catalog"
        if self._looks_like_catalog_entry(chunk):
            return "catalog_entry"
        # 楔子/序章/序幕/引子 若标题行匹配章节边界模式，视为正文
        if any(first_line.startswith(item.lower()) for item in _PROLOGUE_TITLES):
            if self._looks_like_main_chapter_title(title):
                return "main_chapter"
            # 即使标题不匹配主章模式（如纯"楔子"），只要正文够长就视为正文
            body = self._chapter_body_text(chunk)
            if len(body) >= _MIN_CHAPTER_BODY_CHARS:
                return "main_chapter"
            return "prologue"
        if self._looks_like_main_chapter_title(title):
            return "main_chapter"
        return "unknown"

    def _looks_like_main_chapter_title(self, title: str) -> bool:
        """检查标题行是否符合本服务支持的章节标题格式。"""
        return any(compiled.match(title) for compiled, _priority in _COMPILED_PATTERNS)

    def _looks_like_catalog_entry(self, chunk: str) -> bool:
        """目录项通常只有章节标题，没有正文内容，不能当作正文主章节。"""
        lines = [line.strip() for line in chunk.splitlines() if line.strip()]
        return len(lines) == 1 and self._looks_like_main_chapter_title(lines[0])

    def _has_notice_hint_near_start(self, chunk: str, compact: str) -> bool:
        """只把开头声明识别为 notice，避免正文中偶发“下载”等词误杀整章。"""
        lines = [line.strip().lower() for line in chunk.splitlines() if line.strip()]
        head = "".join(lines[:3])
        return any(hint.lower() in head for hint in _NON_STORY_HINTS) or (
            len(compact) <= 240 and any(hint.lower() in compact for hint in _NON_STORY_HINTS)
        )

    @staticmethod
    def _line_range_for_offsets(text: str, start: int, end: int) -> tuple[int, int]:
        start_line = text[:start].count("\n") + 1
        end_line = text[:end].count("\n") + 1
        return start_line, end_line

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

    @classmethod
    def _display_title(cls, chunk: str) -> str:
        title = cls._extract_title(chunk)
        return cls._normalized_main_chapter_title(title)

    @staticmethod
    def _main_chapter_number_key(title: str) -> str | None:
        match = _MAIN_CHAPTER_HEADING_RE.match(title.strip())
        if not match:
            return None
        return match.group("number")

    @classmethod
    def _normalized_main_chapter_title(cls, title: str) -> str:
        match = _MAIN_CHAPTER_HEADING_RE.match(title.strip())
        if not match:
            return title
        number = match.group("number")
        tail = match.group("tail") or ""
        if _SECTION_TAIL_RE.match(tail):
            return f"第{number}章"
        return title.strip()

    @classmethod
    def _chapter_body_text(cls, text: str) -> str:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if not lines:
            return ""
        first_key = cls._main_chapter_number_key(lines[0])
        if first_key:
            body_lines = [line for line in lines if cls._main_chapter_number_key(line) != first_key]
            return "\n".join(body_lines).strip()
        return "\n".join(lines).strip()

    @classmethod
    def _chapter_quality_warnings(cls, title: str, text: str) -> list[SplitWarning]:
        body = cls._chapter_body_text(text)
        if not body:
            return [SplitWarning("chapter.title_only", "章节只有标题，没有可用正文。", title)]
        if len(body) < _MIN_CHAPTER_BODY_CHARS:
            return [SplitWarning("chapter.too_short", "章节正文过短，需要人工复核边界。", title)]
        return []

    @classmethod
    def _same_main_chapter_heading_count(cls, text: str) -> int:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if not lines:
            return 0
        first_key = cls._main_chapter_number_key(lines[0])
        if not first_key:
            return 0
        return sum(1 for line in lines if cls._main_chapter_number_key(line) == first_key)

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

        AI 只建议 line boundary，代码负责切片和后续 ID 生成。
        """
        return self._split_by_ai_with_trace(text).chapters

    def _split_by_ai_with_trace(self, text: str) -> SplitResult:
        """调用轻量 boundary reader，并验证 AI 返回的行号范围。"""
        if self.boundary_reader is None:
            return SplitResult(
                [],
                mode_used="ai",
                warnings=[SplitWarning("chapter_boundary.no_reader", "AI 拆章未配置 boundary reader")],
            )
        ai_plan = self.boundary_reader.run({"line_index": self._line_index(text), "target_main_chapters": 3})
        return self._apply_ai_plan(text, ai_plan)

    @staticmethod
    def _line_index(text: str) -> list[dict[str, Any]]:
        return [{"line": index, "text": line} for index, line in enumerate(text.split("\n"), start=1)]

    def _apply_ai_plan(self, text: str, ai_plan: dict[str, Any]) -> SplitResult:
        """把 AI 边界计划转换为章节，拒绝越界、重叠或空切片。"""
        lines = text.split("\n")
        ranges: list[tuple[int, int, dict[str, Any]]] = []
        ignored = [
            IgnoredSpan(
                kind=str(span.get("kind", "ignored")),
                start_line=int(span.get("start_line", 0) or 0),
                end_line=int(span.get("end_line", span.get("start_line", 0)) or 0),
                reason=str(span.get("reason", "AI boundary reader ignored this span")),
            )
            for span in ai_plan.get("ignored_spans", [])
            if isinstance(span, dict)
        ]
        warnings: list[SplitWarning] = []

        for candidate in ai_plan.get("candidate_chapters", []):
            if not isinstance(candidate, dict) or candidate.get("chapter_kind") != "main_chapter":
                continue
            start_line = int(candidate.get("start_line", 0) or 0)
            end_line = int(candidate.get("end_line", 0) or 0)
            if start_line < 1 or end_line < start_line or end_line > len(lines):
                warnings.append(SplitWarning("chapter_boundary.invalid_range", "AI 返回了越界章节范围"))
                continue
            ranges.append((start_line, end_line, candidate))

        ranges.sort(key=lambda item: item[0])
        for previous, current in zip(ranges, ranges[1:]):
            if current[0] <= previous[1]:
                return SplitResult(
                    [],
                    mode_used="ai",
                    ignored_spans=ignored,
                    warnings=[SplitWarning("chapter_boundary.overlap", "AI 返回了重叠章节范围")],
                    ai_plan=ai_plan,
                )

        chapters: list[SplitChapter] = []
        for start_line, end_line, candidate in ranges[:3]:
            chunk = "\n".join(lines[start_line - 1:end_line]).strip()
            if not chunk:
                warnings.append(SplitWarning("chapter_boundary.empty_chunk", "AI 返回了空章节"))
                continue
            raw_title = candidate.get("title")
            title = raw_title.strip() if isinstance(raw_title, str) and raw_title.strip() else self._extract_title(chunk)
            title = self._normalized_main_chapter_title(title)
            chapters.append(SplitChapter(title=title, text=chunk, order=len(chapters) + 1))
            warnings.extend(self._chapter_quality_warnings(title, chunk))

        if len(chapters) < 3:
            warnings.append(SplitWarning("chapters.too_few_after_ai_split", "AI 拆分后可信正文少于 3 章"))
        return SplitResult(chapters, mode_used="ai", ignored_spans=ignored, warnings=warnings, ai_plan=ai_plan)

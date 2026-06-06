from __future__ import annotations

from app.services.chapter_splitter import ChapterSplitter


class StubBoundaryReader:
    def __init__(self, result: dict) -> None:
        self.result = result
        self.calls = 0

    def run(self, input_data: dict) -> dict:
        self.calls += 1
        return self.result


def test_rule_split_drops_download_site_statement() -> None:
    raw = (
        "声明:本书为八零电子书(txt02.com)的用户自网络收集整理制作,仅供预览交流学习使用。\n\n"
        "第一章 雨夜归来\n林晚推开旧宅大门。\n\n"
        "第二章 旧案重启\n电话在午夜响起。\n\n"
        "第三章 钟声之后\n钟声停下时，信封出现了。"
    )

    result = ChapterSplitter().split(raw, mode="rule")

    assert [chapter.title for chapter in result] == ["第一章 雨夜归来", "第二章 旧案重启", "第三章 钟声之后"]
    assert all(not chapter.title.startswith("声明:") for chapter in result)


def test_rule_split_does_not_count_catalog_as_chapter() -> None:
    raw = (
        "目录\n第一章 雨夜归来\n第二章 旧案重启\n\n"
        "第一章 雨夜归来\n正文一。\n\n"
        "第二章 旧案重启\n正文二。\n\n"
        "第三章 钟声之后\n正文三。"
    )

    result = ChapterSplitter().split(raw, mode="rule")

    assert [chapter.title for chapter in result] == ["第一章 雨夜归来", "第二章 旧案重启", "第三章 钟声之后"]


def test_rule_split_includes_prologue_as_chapter() -> None:
    """序章/前传/楔子也是正文内容的一部分，应被纳入章节列表。"""
    # 构造足够长度的正文以满足 _MIN_CHAPTER_BODY_CHARS (80)
    body = "十" * 100
    raw = (
        f"楔子\n{body}\n\n"
        f"第一章 雨夜归来\n{body}\n\n"
        f"第二章 旧案重启\n{body}\n\n"
        f"第三章 钟声之后\n{body}"
    )

    result = ChapterSplitter().split(raw, mode="rule")

    # 楔子 应作为第一章纳入，后续为 第一章、第二章（第三章被截断因为只取前三章）
    assert [chapter.title for chapter in result] == ["楔子", "第一章 雨夜归来", "第二章 旧案重启"]


def test_auto_split_uses_ai_when_rule_has_too_few_main_chapters() -> None:
    reader = StubBoundaryReader(
        {
            "ignored_spans": [],
            "candidate_chapters": [
                {"chapter_kind": "main_chapter", "title": "", "start_line": 1, "end_line": 1, "confidence": 0.9},
                {"chapter_kind": "main_chapter", "title": "", "start_line": 3, "end_line": 3, "confidence": 0.9},
                {"chapter_kind": "main_chapter", "title": "", "start_line": 5, "end_line": 5, "confidence": 0.9},
            ],
            "warnings": [],
        }
    )
    raw = "雨夜里，林晚回家。\n\n电话响起。\n\n旧信出现。"

    result = ChapterSplitter(boundary_reader=reader).split_with_trace(raw, mode="auto")

    assert reader.calls == 1
    assert result.mode_used == "ai"
    assert len(result.chapters) == 3


def test_ai_plan_with_overlapping_ranges_is_rejected() -> None:
    reader = StubBoundaryReader(
        {
            "candidate_chapters": [
                {"chapter_kind": "main_chapter", "title": "", "start_line": 1, "end_line": 3, "confidence": 0.9},
                {"chapter_kind": "main_chapter", "title": "", "start_line": 2, "end_line": 4, "confidence": 0.9},
                {"chapter_kind": "main_chapter", "title": "", "start_line": 5, "end_line": 6, "confidence": 0.9},
            ]
        }
    )

    result = ChapterSplitter(boundary_reader=reader).split_with_trace("A\nB\nC\nD\nE\nF", mode="ai")

    assert result.chapters == []
    assert any(warning.code == "chapter_boundary.overlap" for warning in result.warnings)


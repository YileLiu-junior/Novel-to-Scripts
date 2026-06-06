from __future__ import annotations

from app.ai.providers.fake_provider import FakeProvider
from app.ai.skills.chapter_boundary_reader import ChapterBoundaryReaderSkill


def test_chapter_boundary_reader_returns_boundary_plan() -> None:
    skill = ChapterBoundaryReaderSkill(FakeProvider())

    result = skill.run(
        {
            "line_index": [
                {"line": 1, "text": "声明:仅供预览交流。"},
                {"line": 2, "text": "雨夜里，林晚回到旧宅。"},
                {"line": 3, "text": "电话在午夜响起。"},
                {"line": 4, "text": "钟声停下时，信封出现了。"},
            ],
            "target_main_chapters": 3,
        }
    )

    assert "candidate_chapters" in result
    assert len(result["candidate_chapters"]) == 3
    assert result["candidate_chapters"][0]["chapter_kind"] == "main_chapter"
    assert result["ignored_spans"][0]["kind"] == "copyright_notice"
    assert "events" not in result
    assert "characters" not in result


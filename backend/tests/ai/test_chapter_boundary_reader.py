from __future__ import annotations

from app.ai.providers.base import StructuredGenerationResult
from app.ai.skills.chapter_boundary_reader import ChapterBoundaryReaderSkill


class _ChapterBoundaryFake:
    """Inline deterministic provider — replaces deleted FakeProvider for tests."""
    name = "fake"

    def generate_structured(self, request):
        lines = request.input_data.get("line_index", [])
        ignored = [
            {"kind": "copyright_notice", "start_line": item["line"], "end_line": item["line"],
             "reason": "fake provider detected non-story notice"}
            for item in lines if "声明" in str(item.get("text", ""))
        ]
        story_lines = [item for item in lines if "声明" not in str(item.get("text", ""))]
        candidates = []
        for idx, item in enumerate(story_lines[:3], start=1):
            candidates.append({
                "chapter_kind": "main_chapter",
                "title": item["text"][:20],
                "start_line": item["line"],
                "end_line": item["line"],
                "confidence": 0.9,
            })
        return StructuredGenerationResult(
            provider=self.name, raw_output=None,
            parsed_output={"ignored_spans": ignored, "candidate_chapters": candidates, "warnings": []},
        )

    def generate_text(self, prompt, temperature=0.0, max_tokens=None):
        return "fake-provider-text-output"


def test_chapter_boundary_reader_returns_boundary_plan() -> None:
    skill = ChapterBoundaryReaderSkill(_ChapterBoundaryFake())

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


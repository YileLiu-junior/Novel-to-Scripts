from __future__ import annotations

from app.services.artifact_service import ArtifactService
from app.services.chapter_intake_service import ChapterIntakeService


class _ChapterBoundaryFake:
    """Inline deterministic provider — replaces deleted FakeProvider for tests."""
    name = "fake"

    def generate_structured(self, request):
        from app.ai.providers.base import StructuredGenerationResult
        lines = request.input_data.get("line_index", [])
        target = request.input_data.get("target_main_chapters", 3)
        story_lines = [(item["line"], item["text"]) for item in lines if item.get("text", "").strip()]
        ignored = [
            {"kind": "copyright_notice", "start_line": item["line"], "end_line": item["line"],
             "reason": "fake provider detected non-story notice"}
            for item in lines if "声明" in str(item.get("text", ""))
        ]
        candidates = []
        for idx, (line_no, text) in enumerate(story_lines[:target], start=1):
            candidates.append({
                "chapter_kind": "main_chapter",
                "title": text[:20],
                "start_line": line_no,
                "end_line": line_no,
                "confidence": 0.9,
            })
        return StructuredGenerationResult(
            provider=self.name, raw_output=None,
            parsed_output={"ignored_spans": ignored, "candidate_chapters": candidates, "warnings": []},
        )

    def generate_text(self, prompt, temperature=0.0, max_tokens=None):
        return "fake-provider-text-output"


class ExplodingProvider:
    name = "exploding"

    def generate_structured(self, request):
        raise AssertionError("provider should not be called when rule split succeeds")

    def generate_text(self, prompt: str, temperature: float = 0.0, max_tokens: int | None = None) -> str:
        raise AssertionError("provider should not be called when rule split succeeds")


def test_auto_split_persists_three_chapters_and_split_artifact(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("XENGINEER_DATA_ROOT", str(tmp_path))
    service = ChapterIntakeService(provider=_ChapterBoundaryFake())

    chapters, trace = service.auto_split_and_save(
        "project_abc",
        "声明:仅供预览交流。\n\n雨夜里，林晚回家。\n\n电话响起。\n\n旧信出现。",
        mode="auto",
    )

    assert len(chapters) == 3
    assert trace["mode_used"] == "ai"

    artifact = ArtifactService().latest_for_project("project_abc", "chapter_split_plan")
    assert artifact is not None
    assert artifact.data["mode_used"] == "ai"


def test_rule_success_does_not_call_provider(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("XENGINEER_DATA_ROOT", str(tmp_path))
    service = ChapterIntakeService(provider=ExplodingProvider())

    chapters, trace = service.auto_split_and_save(
        "project_rule",
        "第一章 雨夜归来\n正文一。\n\n第二章 旧案重启\n正文二。\n\n第三章 钟声之后\n正文三。",
        mode="auto",
    )

    assert len(chapters) == 3
    assert trace["mode_used"] == "rule"

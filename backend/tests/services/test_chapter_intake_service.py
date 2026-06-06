from __future__ import annotations

from app.ai.providers.fake_provider import FakeProvider
from app.services.artifact_service import ArtifactService
from app.services.chapter_intake_service import ChapterIntakeService


class ExplodingProvider:
    name = "exploding"

    def generate_structured(self, request):
        raise AssertionError("provider should not be called when rule split succeeds")

    def generate_text(self, prompt: str, temperature: float = 0.0, max_tokens: int | None = None) -> str:
        raise AssertionError("provider should not be called when rule split succeeds")


def test_auto_split_persists_three_chapters_and_split_artifact(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("XENGINEER_DATA_ROOT", str(tmp_path))
    service = ChapterIntakeService(provider=FakeProvider())

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

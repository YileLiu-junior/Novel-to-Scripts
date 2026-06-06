"""E2E test for the FULL pipeline: raw novel txt → chapter intake → screenplay YAML.

Tests the complete backend chain:
    1. Read raw novel text from docs/
    2. ChapterIntakeService.auto_split_and_save() — split into chapters
    3. GenerationOrchestrator.run_v1() — 4-stage AI pipeline
    4. Verify structural validity of output

REQUIRES:
    DEEPSEEK_API_KEY          — valid DeepSeek API key

Setup (one-time per terminal session):
    . .\\scripts\\configure_deepseek_env.ps1

Run:
    python -m pytest tests/ai/test_full_flow_e2e.py -v

Not for CI — uses real API calls (chapter boundary detection + 4 pipeline stages).
"""

from __future__ import annotations

import os
import unittest
from pathlib import Path
from typing import Any

from app.ai.skills.adaptation_planner import AdaptationPlannerSkill
from app.ai.skills.novel_reader import NovelReaderSkill
from app.ai.skills.screenplay_writer import ScreenplayYamlWriterSkill
from app.ai.skills.story_ontology import StoryOntologySkill
from app.core.settings import AiSettings
from app.domain.adaptation import AdaptationConfig
from app.services.artifact_service import ArtifactService
from app.services.chapter_intake_service import ChapterIntakeService
from app.services.generation_orchestrator import GenerationOrchestrator
from app.services.job_service import JobService
from app.services.llm_trace_service import LlmTraceService
from app.services.project_service import ProjectService
from app.services.validation_service import ValidationService
from app.services.yaml_service import YamlService
from app.repositories.file_store import default_data_root

_REPO_ROOT = Path(__file__).resolve().parents[3]
_NOVEL_PATH = _REPO_ROOT / "docs" / "三生三世十里桃花.txt"
# Take first ~200KB to capture 6-8 chapters
_MAX_BYTES = 200_000


def _has_valid_api_key() -> bool:
    key = os.getenv("DEEPSEEK_API_KEY", "")
    return bool(key) and key != "PASTE_YOUR_DEEPSEEK_API_KEY_HERE"


@unittest.skipUnless(
    _has_valid_api_key(),
    "Set DEEPSEEK_API_KEY to run E2E tests. "
    "Run: . .\\scripts\\configure_deepseek_env.ps1",
)
class FullFlowE2ETest(unittest.TestCase):
    """E2E: raw txt → chapter intake → run_v1() → validated YAML."""

    @classmethod
    def setUpClass(cls) -> None:
        if not _NOVEL_PATH.exists():
            raise unittest.SkipTest(f"Novel file not found: {_NOVEL_PATH}")

        from datetime import datetime
        _ts = datetime.now().strftime("%m%d-%H%M")
        cls.project_id = f"E2E-FullFlow-{_ts}"
        cls.project_svc = ProjectService()
        cls.project = cls.project_svc.create_project(
            title=f"E2E-FullFlow-{_ts}",
            logline="三生三世十里桃花 前3章 完整链路测试",
            target_format="web_series",
            project_id=cls.project_id,
        )

        cls.settings = AiSettings(
            provider="deepseek",
            deepseek_api_key=os.getenv("DEEPSEEK_API_KEY", ""),
        )

    def setUp(self) -> None:
        self.job_service = JobService()
        self.artifact_service = ArtifactService()
        self.llm_trace_service = LlmTraceService()
        self.validation_service = ValidationService()
        self.yaml_service = YamlService(validation_service=self.validation_service)

    # ── helpers ───────────────────────────────────────────────────────

    def _assert_structure_valid(self, job: Any,
                                 screenplay: dict[str, Any],
                                 yaml_text: str) -> None:
        """Core structural assertions valid for any LLM output."""
        self.assertEqual(job.status, "succeeded",
                         f"Job failed: {getattr(job, 'error', 'unknown')}")

        self.assertTrue(yaml_text and yaml_text.strip(),
                        "YAML output must not be empty")

        self.assertIn("schema_version", screenplay)
        self.assertIn("scenes", screenplay)
        self.assertIn("story_bible", screenplay)
        self.assertIn("events", screenplay)

        self.assertIsInstance(screenplay["scenes"], list)
        self.assertGreater(len(screenplay["scenes"]), 0,
                           "screenplay must have at least one scene")

        # No placeholder content
        screenplay_str = str(screenplay)
        for placeholder in ("Fake Provider", "当前项目主角", "TODO"):
            self.assertNotIn(placeholder, screenplay_str,
                             f"Output must not contain '{placeholder}'")

        # Story bible has characters with names
        story_bible = screenplay.get("story_bible", {})
        self.assertIsInstance(story_bible, dict)
        characters = story_bible.get("characters", [])
        self.assertIsInstance(characters, list)
        self.assertGreater(len(characters), 0)

        names = [c.get("name") for c in characters
                 if isinstance(c, dict) and c.get("name")]
        self.assertGreater(len(names), 0,
                           "At least one character must have a name")

        # Audit report exists
        audit = screenplay.get("audit_report", {})
        self.assertIsInstance(audit, dict)

    def _assert_artifacts_exist(self) -> None:
        """Verify key artifacts were written."""
        artifact_dir = default_data_root() / "projects" / self.project_id / "artifacts"
        self.assertTrue(artifact_dir.exists(),
                        f"Artifact dir must exist: {artifact_dir}")

        for atype in ("story_bible", "screenplay_yaml", "audit_report",
                       "novel_analysis", "adaptation_plan", "screenplay_json"):
            files = list(artifact_dir.glob(f"{atype}_v*.json")) + \
                    list(artifact_dir.glob(f"{atype}_v*.yaml"))
            self.assertGreater(len(files), 0,
                               f"Must have artifact '{atype}' in {artifact_dir}")

    def _assert_chapter_text_stripped(self) -> None:
        """Verify stored artifacts strip full chapter text."""
        import json as _json
        artifact_dir = default_data_root() / "projects" / self.project_id / "artifacts"

        for atype in ("novel_analysis", "story_bible"):
            files = sorted(artifact_dir.glob(f"{atype}_v*.json"))
            if not files:
                continue
            data = _json.loads(files[-1].read_text(encoding="utf-8"))
            for key in ("chapters", "chapters_used"):
                chapters = data.get(key)
                if not isinstance(chapters, list):
                    continue
                for ch in chapters:
                    if not isinstance(ch, dict):
                        continue
                    self.assertNotIn("text", ch,
                                     f"{atype}/{key}: text must be stripped")
                    self.assertNotIn("paragraphs", ch,
                                     f"{atype}/{key}: paragraphs must be stripped")
                    self.assertIn("paragraph_count", ch,
                                  f"{atype}/{key}: must have paragraph_count")

    # ── the test ──────────────────────────────────────────────────────

    def test_full_flow_txt_to_screenplay(self) -> None:
        """E2E: raw novel text → chapter intake → AI pipeline → validated YAML."""
        raw_text = _NOVEL_PATH.read_text(encoding="utf-8")[:_MAX_BYTES]
        self.assertGreater(len(raw_text), 1000,
                           "Novel text must be substantial")

        print(f"\n[E2E-FullFlow] Read {len(raw_text)} chars from novel")

        # Step 1: Chapter intake — split raw text into chapters
        intake = ChapterIntakeService(
            chapter_service=None,  # uses defaults
            artifact_service=self.artifact_service,
        )
        chapters, trace = intake.auto_split_and_save(
            self.project_id, raw_text, mode="auto",
            save_intermediates=True,
        )
        print(f"[E2E-FullFlow] Split into {len(chapters)} chapters "
              f"(mode={trace.get('mode_used', 'unknown')})")
        self.assertGreaterEqual(len(chapters), 3,
                                f"Expected >= 3 chapters, got {len(chapters)}")

        # Step 2: Run the AI pipeline
        from app.ai.providers.factory import build_ai_provider
        provider = build_ai_provider(self.settings)
        orchestrator = GenerationOrchestrator(
            novel_reader=NovelReaderSkill(provider),
            story_ontology=StoryOntologySkill(provider),
            adaptation_planner=AdaptationPlannerSkill(provider),
            screenplay_writer=ScreenplayYamlWriterSkill(provider),
            artifact_service=self.artifact_service,
            job_service=self.job_service,
            llm_trace_service=self.llm_trace_service,
            validation_service=self.validation_service,
            yaml_service=self.yaml_service,
        )

        chapter_dicts = [ch.model_dump(mode="json") for ch in chapters]
        adapt_config = AdaptationConfig(
            target_format="web_series",
            fidelity_level="high",
        )

        print("[E2E-FullFlow] Running pipeline (may take 45-90 seconds)...")
        job = orchestrator.run_v1(
            project_id=self.project_id,
            chapters=chapter_dicts,
            adaptation_config=adapt_config,
            save_intermediates=True,
        )

        print(f"[E2E-FullFlow] Job status: {job.status}")

        # Step 3: Verify outputs
        latest_yaml = self.artifact_service.latest_for_project(
            self.project_id, "screenplay_yaml"
        )
        self.assertIsNotNone(latest_yaml, "screenplay_yaml must exist")
        yaml_text = latest_yaml.data if isinstance(latest_yaml.data, str) \
            else str(latest_yaml.data)

        latest_json = self.artifact_service.latest_for_project(
            self.project_id, "screenplay_json"
        )
        self.assertIsNotNone(latest_json, "screenplay_json must exist")
        screenplay = latest_json.data if isinstance(latest_json.data, dict) else {}

        self._assert_structure_valid(job, screenplay, yaml_text)
        self._assert_artifacts_exist()
        self._assert_chapter_text_stripped()

        print("[E2E-FullFlow] All assertions passed ✓")


if __name__ == "__main__":
    unittest.main()

"""E2E test for the GenerationOrchestrator.run_v1() pipeline with real DeepSeek AI.

Runs the full 4-stage pipeline (novel_reader → story_ontology → adaptation_planner
→ screenplay_writer) against the first ~8 chapters of a real novel.

REQUIRES:
    DEEPSEEK_API_KEY          — valid DeepSeek API key

Setup (one-time per terminal session):
    . .\scripts\configure_deepseek_env.ps1

Run:
    python -m pytest tests/ai/test_pipeline_e2e.py -v

Not for CI — uses real API calls that cost money and take 30-60 seconds.
"""

from __future__ import annotations

import os
import re
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
from app.services.chapter_service import ChapterService
from app.services.generation_orchestrator import GenerationOrchestrator
from app.services.job_service import JobService
from app.services.llm_trace_service import LlmTraceService
from app.services.project_service import ProjectService
from app.services.validation_service import ValidationService
from app.repositories.file_store import default_data_root
from app.services.yaml_service import YamlService

_REPO_ROOT = Path(__file__).resolve().parents[3]
_NOVEL_PATH = _REPO_ROOT / "docs" / "三生三世十里桃花.txt"


def _has_valid_api_key() -> bool:
    key = os.getenv("DEEPSEEK_API_KEY", "")
    return bool(key) and key != "PASTE_YOUR_DEEPSEEK_API_KEY_HERE"

# ── helpers ──────────────────────────────────────────────────────────────

# Regex patterns for chapter boundaries.
# _CHAPTER_BOUNDARY_RE is tighter than ChapterSplitter's patterns — it only
# matches unambiguous chapter/section headers to avoid false positives on
# short numerals and standalone punctuation.
_CHAPTER_BOUNDARY_RE = re.compile(
    r"^\s*(?:"
    r"第[零一二三四五六七八九十百千万\d]+[章节回卷部集]"  # 第X章/第X节/第X回
    r"|前[传序言][\s（(]*[零一二三四五六七八九十百千万\d]*"  # 前传（一）/ 序章
    r"|序[章言]"                                              # 序章/序言
    r"|楔[子文]"                                              # 楔子/楔文
    r"|引[子言文]"                                            # 引子/引言/引文
    r")",
    re.MULTILINE,
)

# Minimum characters for a chunk to be treated as a real chapter
_MIN_CHAPTER_CHARS = 500

# Lines to skip: copyright notices, uploader tags, etc.
_SKIP_HINTS = (
    "声明", "版权", "仅供预览", "请支持正版", "txt02.com",
    "本站", "下载", "手机阅读", "用户上传",
)


def _is_skip_chunk(text: str) -> bool:
    """Return True if the chunk is a copyright/boilerplate block to skip."""
    head = text[:300].lower()
    return any(hint.lower() in head for hint in _SKIP_HINTS)


def _split_novel_for_e2e(
    text: str, max_chapters: int = 8
) -> list[dict[str, str]]:
    """Split raw novel text into chapter chunks, including prologues.

    Uses a tight regex to find chapter-start lines, then slices the text
    into chunks. Filters out copyright boilerplate and tiny chunks
    (false-positive boundary matches). Returns list of {title, text} dicts
    suitable for ChapterService.normalize_chapters().
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    # Find all chapter-start positions
    positions: list[int] = [0]
    for m in _CHAPTER_BOUNDARY_RE.finditer(text):
        pos = m.start()
        # Only add if the match is at the start of a line
        if pos == 0 or text[pos - 1] == "\n":
            positions.append(pos)

    # Sort and deduplicate
    positions = sorted(set(positions))

    # Extract chunks
    chunks: list[dict[str, str]] = []
    for i, start in enumerate(positions):
        end = positions[i + 1] if i + 1 < len(positions) else len(text)
        chunk_text = text[start:end].strip()
        if not chunk_text:
            continue

        # Skip boilerplate
        if _is_skip_chunk(chunk_text):
            continue

        # Skip tiny chunks (false-positive boundary matches)
        if len(chunk_text) < _MIN_CHAPTER_CHARS:
            continue

        # Extract title from first line
        first_line = chunk_text.split("\n", 1)[0].strip()
        # Clean up markdown heading markers
        first_line = re.sub(r"^#+\s*", "", first_line)
        if len(first_line) > 80:
            first_line = first_line[:77] + "..."

        title = first_line or "未命名章节"
        chunks.append({"title": title, "text": chunk_text})

        if len(chunks) >= max_chapters:
            break

    return chunks


def _prepare_chapters(chunks: list[dict[str, str]]) -> list[dict[str, Any]]:
    """Convert raw {title, text} chunks to Chapter dicts via ChapterService."""
    svc = ChapterService()
    chapters = svc.normalize_chapters(chunks)
    return [ch.model_dump(mode="json") for ch in chapters]


def _read_novel_text() -> str:
    """Read the novel file, returning the first ~200KB for E2E testing."""
    raw = _NOVEL_PATH.read_text(encoding="utf-8")
    # Take first ~200KB to cover 6-8 chapters
    return raw[:200_000]


# ── test ─────────────────────────────────────────────────────────────────

@unittest.skipUnless(
    _has_valid_api_key(),
    "Set DEEPSEEK_API_KEY to run E2E tests. "
    "Run: . .\\scripts\\configure_deepseek_env.ps1",
)
class PipelineE2ETest(unittest.TestCase):
    """E2E: GenerationOrchestrator.run_v1() with real DeepSeek."""

    @classmethod
    def setUpClass(cls) -> None:
        if not _NOVEL_PATH.exists():
            raise unittest.SkipTest(f"Novel file not found: {_NOVEL_PATH}")

        from datetime import datetime
        _ts = datetime.now().strftime("%m%d-%H%M")
        cls.project_id = f"E2E-Pipeline-{_ts}"
        cls.project_svc = ProjectService()
        cls.project = cls.project_svc.create_project(
            title=f"E2E-Pipeline-{_ts}",
            logline="三生三世十里桃花 前3章 仙侠爱情 三世纠葛",
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

    # ── build orchestrator ────────────────────────────────────────────

    def _build_orchestrator(self) -> GenerationOrchestrator:
        from app.ai.providers.factory import build_ai_provider
        provider = build_ai_provider(self.settings)
        return GenerationOrchestrator(
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

    # ── helpers ───────────────────────────────────────────────────────

    def _assert_structure_valid(self, job: Any,
                                 screenplay: dict[str, Any],
                                 yaml_text: str) -> None:
        """Core structural assertions valid for any LLM output."""
        # Job completed
        self.assertEqual(job.status, "succeeded",
                         f"Job failed with error: {getattr(job, 'error', 'unknown')}")

        # YAML is non-empty
        self.assertTrue(yaml_text and yaml_text.strip(),
                        "YAML output must not be empty")

        # Top-level schema keys
        self.assertIn("schema_version", screenplay,
                      "screenplay must have schema_version")
        self.assertIn("scenes", screenplay,
                      "screenplay must have scenes")
        self.assertIn("story_bible", screenplay,
                      "screenplay must have story_bible")
        self.assertIn("events", screenplay,
                      "screenplay must have events")
        self.assertIn("project", screenplay,
                      "screenplay must have project")

        # Scenes is a list
        self.assertIsInstance(screenplay["scenes"], list,
                              "scenes must be a list")
        self.assertGreater(len(screenplay["scenes"]), 0,
                           "screenplay must have at least one scene")

        # Not placeholder content
        screenplay_str = str(screenplay)
        self.assertNotIn("Fake Provider", screenplay_str,
                         "Output must not contain 'Fake Provider' placeholder")
        self.assertNotIn("当前项目主角", screenplay_str,
                         "Output must not contain '当前项目主角' placeholder")
        self.assertNotIn("TODO", screenplay_str,
                         "Output must not contain 'TODO' placeholder")

        # Story bible has characters
        story_bible = screenplay.get("story_bible", {})
        self.assertIsInstance(story_bible, dict,
                              "story_bible must be a dict")
        characters = story_bible.get("characters", [])
        self.assertIsInstance(characters, list)
        self.assertGreater(len(characters), 0,
                           "story_bible must have at least one character")

        # Audit report
        audit = screenplay.get("audit_report", {})
        self.assertIsInstance(audit, dict,
                              "audit_report must be a dict")

        # At least one character has a real name
        names = [
            c.get("name", "")
            for c in characters
            if isinstance(c, dict) and c.get("name")
        ]
        self.assertGreater(len(names), 0,
                           "At least one character must have a name")

    def _assert_artifacts_saved(self) -> None:
        """Verify intermediate artifacts were written to disk."""
        artifact_dir = default_data_root() / "projects" / self.project_id / "artifacts"
        self.assertTrue(artifact_dir.exists(),
                        f"Artifact dir must exist: {artifact_dir}")

        expected_types = [
            "story_bible",
            "screenplay_yaml",
            "audit_report",
            # save_intermediates=True extras:
            "novel_analysis",
            "adaptation_plan",
            "screenplay_json",
        ]
        for atype in expected_types:
            files = list(artifact_dir.glob(f"{atype}_v*.json")) + \
                    list(artifact_dir.glob(f"{atype}_v*.yaml"))
            self.assertGreater(len(files), 0,
                               f"Must have at least one artifact of type '{atype}' in {artifact_dir}")

    def _assert_chapter_text_stripped(self) -> None:
        """Verify stored novel_analysis and story_bible have chapter text stripped."""
        import json as _json
        artifact_dir = default_data_root() / "projects" / self.project_id / "artifacts"

        for atype in ("novel_analysis", "story_bible"):
            files = sorted(artifact_dir.glob(f"{atype}_v*.json"))
            if not files:
                continue
            data = _json.loads(files[-1].read_text(encoding="utf-8"))
            # Check chapter data has paragraph_count but not full text
            for key in ("chapters", "chapters_used"):
                chapters = data.get(key)
                if not isinstance(chapters, list):
                    continue
                for ch in chapters:
                    if not isinstance(ch, dict):
                        continue
                    self.assertNotIn("text", ch,
                                     f"{atype}/{key}: full text must be stripped (found 'text')")
                    self.assertNotIn("paragraphs", ch,
                                     f"{atype}/{key}: paragraphs array must be stripped")
                    self.assertIn("paragraph_count", ch,
                                  f"{atype}/{key}: must have paragraph_count reference")

    # ── the test ──────────────────────────────────────────────────────

    def test_run_v1_pipeline_with_real_ai(self) -> None:
        """E2E: run_v1() processes 6-8 chapters end-to-end with real DeepSeek."""
        raw_text = _read_novel_text()
        chunks = _split_novel_for_e2e(raw_text, max_chapters=8)
        self.assertGreaterEqual(len(chunks), 3,
                                f"Expected >= 3 chapters from novel, got {len(chunks)}")
        print(f"\n[E2E] Split {len(chunks)} chapters from novel")

        chapters = _prepare_chapters(chunks)
        print(f"[E2E] Prepared {len(chapters)} chapters for pipeline")

        orchestrator = self._build_orchestrator()
        adapt_config = AdaptationConfig(
            target_format="web_series",
            fidelity_level="high",
        )

        print("[E2E] Running pipeline (this may take 30-60 seconds)...")
        job = orchestrator.run_v1(
            project_id=self.project_id,
            chapters=chapters,
            adaptation_config=adapt_config,
            save_intermediates=True,
        )

        # ── assertions ────────────────────────────────────────────────
        print(f"[E2E] Job status: {job.status}")

        # Read the produced YAML
        latest_yaml = self.artifact_service.latest_for_project(
            self.project_id, "screenplay_yaml"
        )
        self.assertIsNotNone(latest_yaml, "screenplay_yaml artifact must exist")
        yaml_text = latest_yaml.data if isinstance(latest_yaml.data, str) \
            else str(latest_yaml.data)

        # Read the produced screenplay JSON
        latest_json = self.artifact_service.latest_for_project(
            self.project_id, "screenplay_json"
        )
        self.assertIsNotNone(latest_json, "screenplay_json artifact must exist")
        screenplay = latest_json.data if isinstance(latest_json.data, dict) \
            else {}

        self._assert_structure_valid(job, screenplay, yaml_text)
        self._assert_artifacts_saved()
        self._assert_chapter_text_stripped()

        print("[E2E] All assertions passed - OK")


if __name__ == "__main__":
    unittest.main()

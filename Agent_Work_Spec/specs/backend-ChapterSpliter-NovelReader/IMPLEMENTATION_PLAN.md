# ChapterSplitter NovelReader Boundary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a reliable backend-only raw text intake flow that filters non-story text, identifies the first three main novel chapters, and keeps NovelReader source-backed analysis after stable chapter and paragraph IDs exist.

**Architecture:** `ChapterSplitter` remains the pure boundary slicer. A new `ChapterBoundaryReaderSkill` provides AI boundary suggestions only when rules cannot produce three trusted main chapters. A new `ChapterIntakeService` orchestrates auto-split, artifact trace, and chapter persistence while the public frontend DTO stays unchanged.

**Tech Stack:** Python, FastAPI, Pydantic v2, local file repositories, existing `AiProvider` / `SkillWrapper`, pytest.

---

## File Structure

Create:

- `backend/app/ai/skills/chapter_boundary_reader.py`：轻量 AI boundary reader wrapper。
- `backend/app/ai/prompts/chapter_boundary_reader.md`：只输出章节边界计划的 prompt。
- `backend/app/services/chapter_intake_service.py`：协调 auto-split、artifact trace、chapter persistence。
- `backend/tests/services/test_chapter_splitter.py`：规则拆分和边界校验单元测试。
- `backend/tests/services/test_chapter_intake_service.py`：auto-split orchestration 测试。
- `backend/tests/ai/test_chapter_boundary_reader.py`：fake provider boundary reader contract 测试。
- `backend/tests/api/test_chapters_auto_split.py`：API 契约保持测试。

Modify:

- `backend/app/services/chapter_splitter.py`：新增非正文过滤、三章正文策略、AI plan 应用和 warning 结构。
- `backend/app/api/routes_chapters.py`：路由改为调度 `ChapterIntakeService`。
- `backend/app/ai/skills/__init__.py`：导出 `ChapterBoundaryReaderSkill`。
- `backend/app/ai/providers/fake_provider.py`：支持 `chapter_boundary_reader` 的确定性 fake 输出。
- `backend/app/domain/artifacts.py`：新增 `chapter_split_plan` artifact type。
- `fixtures/前端接入指南.md`：说明 `auto-split` 响应形状不变，AI trace 通过 artifact 查看。
- `BACKEND_UNIMPLEMENTED_VERSION_MAP.md`：把 `_split_by_ai` 从占位改为计划中的 V0 增强项。

---

### Task 1: Define Split Plan Data Structures

**Files:**
- Modify: `backend/app/services/chapter_splitter.py`
- Test: `backend/tests/services/test_chapter_splitter.py`

- [ ] **Step 1: Write failing tests for preamble filtering**

```python
from app.services.chapter_splitter import ChapterSplitter


def test_rule_split_drops_download_site_statement() -> None:
    raw = (
        "声明:本书为八零电子书(txt02.com)的用户自网络收集整理制作,仅供预览交流学习使用。\\n\\n"
        "第一章 雨夜归来\\n林晚推开旧宅大门。\\n\\n"
        "第二章 旧案重启\\n电话在午夜响起。\\n\\n"
        "第三章 钟声之后\\n钟声停下时，信封出现了。"
    )

    result = ChapterSplitter().split(raw, mode="rule")

    assert [chapter.title for chapter in result] == ["第一章 雨夜归来", "第二章 旧案重启", "第三章 钟声之后"]
    assert all(not chapter.title.startswith("声明:") for chapter in result)
```

- [ ] **Step 2: Run the failing test**

Run: `pytest backend/tests/services/test_chapter_splitter.py::test_rule_split_drops_download_site_statement -q`

Expected: FAIL because current `_find_boundaries()` inserts `0` and slices the statement as chapter 1.

- [ ] **Step 3: Add internal result structures**

Add near `SplitChapter`:

```python
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
```

- [ ] **Step 4: Keep public `split()` compatibility**

Keep `split()` returning `list[SplitChapter]` and add `split_with_trace()`:

```python
def split(self, raw_text: str, mode: str = "auto") -> list[SplitChapter]:
    return self.split_with_trace(raw_text, mode).chapters


def split_with_trace(self, raw_text: str, mode: str = "auto") -> SplitResult:
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
```

- [ ] **Step 5: Run the test again**

Run: `pytest backend/tests/services/test_chapter_splitter.py -q`

Expected: PASS for the new test and no regression for existing split callers.

---

### Task 2: Implement Rule-Based Main Chapter Filtering

**Files:**
- Modify: `backend/app/services/chapter_splitter.py`
- Test: `backend/tests/services/test_chapter_splitter.py`

- [ ] **Step 1: Add failing tests for catalog and prologue**

```python
def test_rule_split_does_not_count_catalog_as_chapter() -> None:
    raw = (
        "目录\\n第一章 雨夜归来\\n第二章 旧案重启\\n\\n"
        "第一章 雨夜归来\\n正文一。\\n\\n"
        "第二章 旧案重启\\n正文二。\\n\\n"
        "第三章 钟声之后\\n正文三。"
    )

    result = ChapterSplitter().split(raw, mode="rule")

    assert [chapter.title for chapter in result] == ["第一章 雨夜归来", "第二章 旧案重启", "第三章 钟声之后"]


def test_rule_split_does_not_count_prologue_as_main_chapter() -> None:
    raw = (
        "楔子\\n十年前的大火没有熄灭。\\n\\n"
        "第一章 雨夜归来\\n正文一。\\n\\n"
        "第二章 旧案重启\\n正文二。\\n\\n"
        "第三章 钟声之后\\n正文三。"
    )

    result = ChapterSplitter().split(raw, mode="rule")

    assert [chapter.title for chapter in result] == ["第一章 雨夜归来", "第二章 旧案重启", "第三章 钟声之后"]
```

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest backend/tests/services/test_chapter_splitter.py::test_rule_split_does_not_count_catalog_as_chapter backend/tests/services/test_chapter_splitter.py::test_rule_split_does_not_count_prologue_as_main_chapter -q`

Expected: FAIL until filtering is implemented.

- [ ] **Step 3: Add classifier helpers**

```python
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

_CATALOG_TITLES = ("目录", "目 录", "contents", "CONTENT")
_PROLOGUE_TITLES = ("序章", "序", "楔子", "前言", "引子")


def _classify_chunk(self, chunk: str) -> str:
    first_line = self._extract_title(chunk).lower()
    compact = re.sub(r"\s+", "", chunk.lower())
    if any(hint.lower() in compact for hint in _NON_STORY_HINTS):
        return "ignored_notice"
    if any(first_line == title.lower() for title in _CATALOG_TITLES):
        return "catalog"
    if any(first_line.startswith(title.lower()) for title in _PROLOGUE_TITLES):
        return "prologue"
    if self._looks_like_main_chapter_title(self._extract_title(chunk)):
        return "main_chapter"
    return "unknown"


def _looks_like_main_chapter_title(self, title: str) -> bool:
    return any(compiled.match(title) for compiled, _priority in _COMPILED_PATTERNS)
```

- [ ] **Step 4: Change rule slicing to drop non-story chunks and keep first 3 main chapters**

```python
def _split_by_rules_with_trace(self, text: str) -> SplitResult:
    boundaries = self._find_boundaries(text)
    if len(boundaries) < 2:
        return SplitResult(self._single_chapter(text), mode_used="rule")

    chapters: list[SplitChapter] = []
    ignored: list[IgnoredSpan] = []
    warnings: list[SplitWarning] = []
    for i, start in enumerate(boundaries):
        end = boundaries[i + 1] if i + 1 < len(boundaries) else len(text)
        chunk = text[start:end].strip()
        if not chunk:
            continue
        kind = self._classify_chunk(chunk)
        if kind != "main_chapter":
            start_line = text[:start].count("\n") + 1
            end_line = text[:end].count("\n") + 1
            ignored.append(IgnoredSpan(kind, start_line, end_line, "不计入正文前三章"))
            continue
        chapters.append(SplitChapter(title=self._extract_title(chunk), text=chunk, order=len(chapters) + 1))
        if len(chapters) == 3:
            break

    if len(chapters) < 3:
        warnings.append(SplitWarning("chapters.too_few_after_rule_split", "规则拆分后可信正文少于 3 章"))
    return SplitResult(chapters, mode_used="rule", ignored_spans=ignored, warnings=warnings)
```

- [ ] **Step 5: Run rule splitter tests**

Run: `pytest backend/tests/services/test_chapter_splitter.py -q`

Expected: PASS.

---

### Task 3: Add ChapterBoundaryReaderSkill

**Files:**
- Create: `backend/app/ai/skills/chapter_boundary_reader.py`
- Create: `backend/app/ai/prompts/chapter_boundary_reader.md`
- Modify: `backend/app/ai/skills/__init__.py`
- Modify: `backend/app/ai/providers/fake_provider.py`
- Test: `backend/tests/ai/test_chapter_boundary_reader.py`

- [ ] **Step 1: Write skill wrapper test**

```python
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
```

- [ ] **Step 2: Run test to verify failure**

Run: `pytest backend/tests/ai/test_chapter_boundary_reader.py -q`

Expected: FAIL because the skill does not exist.

- [ ] **Step 3: Create wrapper**

```python
from __future__ import annotations

from app.ai.skills.base import SkillWrapper


class ChapterBoundaryReaderSkill(SkillWrapper):
    """AI raw txt 边界识别 skill，只建议章节范围，不提取故事资产。"""

    skill_name = "chapter_boundary_reader"
    prompt_name = "chapter_boundary_reader.md"
```

- [ ] **Step 4: Add prompt**

```markdown
# ChapterBoundaryReaderSkill Prompt Reference

## Role

Identify non-story spans and the first three main chapter boundaries from normalized raw novel text.

## Input Shape

```json
{
  "line_index": [{"line": 1, "text": "string"}],
  "target_main_chapters": 3
}
```

## Output Shape

```json
{
  "ignored_spans": [],
  "candidate_chapters": [],
  "warnings": []
}
```

## Constraints

- Only identify boundaries.
- Do not write scenes, dialogue, events, characters, conflicts, foreshadowing, or summaries.
- `start_line` and `end_line` must refer to input line numbers.
- Mark copyright notices, download-site text, catalogs, prefaces, prologues, and ads as `ignored_spans`.
- Return at most three `main_chapter` candidates.
- If the original text has no chapter title, leave `title` as an empty string.
```

- [ ] **Step 5: Export skill**

Add to `backend/app/ai/skills/__init__.py`:

```python
from app.ai.skills.chapter_boundary_reader import ChapterBoundaryReaderSkill
```

and include `"ChapterBoundaryReaderSkill"` in `__all__`.

- [ ] **Step 6: Add fake provider branch**

In `FakeProvider._default_payload`:

```python
if request.skill_name == "chapter_boundary_reader":
    return self._build_chapter_boundary_plan(request.input_data)
```

Add deterministic builder:

```python
def _build_chapter_boundary_plan(self, input_data: dict[str, Any]) -> dict[str, Any]:
    lines = [item for item in input_data.get("line_index", []) if isinstance(item, dict)]
    ignored = []
    story_lines = []
    for item in lines:
        text = str(item.get("text", ""))
        line_no = int(item.get("line", 0) or 0)
        if "声明" in text or "txt02.com" in text or "仅供预览" in text:
            ignored.append(
                {
                    "kind": "copyright_notice",
                    "start_line": line_no,
                    "end_line": line_no,
                    "reason": "fake provider detected non-story notice",
                }
            )
        elif text.strip():
            story_lines.append(line_no)
    candidates = []
    for idx, line_no in enumerate(story_lines[:3], start=1):
        candidates.append(
            {
                "chapter_kind": "main_chapter",
                "title": "",
                "start_line": line_no,
                "end_line": line_no,
                "confidence": 0.8,
            }
        )
    return {"ignored_spans": ignored, "candidate_chapters": candidates, "warnings": []}
```

- [ ] **Step 7: Run skill test**

Run: `pytest backend/tests/ai/test_chapter_boundary_reader.py -q`

Expected: PASS.

---

### Task 4: Apply AI Boundary Plans Safely

**Files:**
- Modify: `backend/app/services/chapter_splitter.py`
- Test: `backend/tests/services/test_chapter_splitter.py`

- [ ] **Step 1: Write tests for AI fallback and invalid AI plans**

```python
class StubBoundaryReader:
    def __init__(self, result):
        self.result = result
        self.calls = 0

    def run(self, input_data):
        self.calls += 1
        return self.result


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
    raw = "雨夜里，林晚回家。\\n\\n电话响起。\\n\\n旧信出现。"

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

    result = ChapterSplitter(boundary_reader=reader).split_with_trace("A\\nB\\nC\\nD\\nE\\nF", mode="ai")

    assert result.chapters == []
    assert any(warning.code == "chapter_boundary.overlap" for warning in result.warnings)
```

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest backend/tests/services/test_chapter_splitter.py -q`

Expected: FAIL until AI plan application exists.

- [ ] **Step 3: Accept a boundary reader in `ChapterSplitter.__init__`**

```python
def __init__(self, ai_provider: Any | None = None, boundary_reader: Any | None = None) -> None:
    self.ai_provider = ai_provider
    self.boundary_reader = boundary_reader
```

- [ ] **Step 4: Add line index and AI application helpers**

```python
def _line_index(self, text: str) -> list[dict[str, Any]]:
    return [{"line": index, "text": line} for index, line in enumerate(text.split("\n"), start=1)]


def _split_by_ai_with_trace(self, text: str) -> SplitResult:
    if self.boundary_reader is None:
        return SplitResult([], mode_used="ai", warnings=[
            SplitWarning("chapter_boundary.no_reader", "AI 拆章未配置 boundary reader")
        ])
    ai_plan = self.boundary_reader.run({"line_index": self._line_index(text), "target_main_chapters": 3})
    return self._apply_ai_plan(text, ai_plan)
```

- [ ] **Step 5: Validate AI ranges before slicing**

```python
def _apply_ai_plan(self, text: str, ai_plan: dict[str, Any]) -> SplitResult:
    lines = text.split("\n")
    ranges: list[tuple[int, int, dict[str, Any]]] = []
    warnings: list[SplitWarning] = []
    for candidate in ai_plan.get("candidate_chapters", []):
        if candidate.get("chapter_kind") != "main_chapter":
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
            return SplitResult([], mode_used="ai", warnings=[
                SplitWarning("chapter_boundary.overlap", "AI 返回了重叠章节范围")
            ], ai_plan=ai_plan)

    chapters: list[SplitChapter] = []
    for start_line, end_line, candidate in ranges[:3]:
        chunk = "\n".join(lines[start_line - 1:end_line]).strip()
        if not chunk:
            warnings.append(SplitWarning("chapter_boundary.empty_chunk", "AI 返回了空章节"))
            continue
        raw_title = candidate.get("title")
        title = raw_title.strip() if isinstance(raw_title, str) and raw_title.strip() else self._extract_title(chunk)
        chapters.append(SplitChapter(title=title, text=chunk, order=len(chapters) + 1))
    return SplitResult(chapters, mode_used="ai", warnings=warnings, ai_plan=ai_plan)
```

- [ ] **Step 6: Run splitter tests**

Run: `pytest backend/tests/services/test_chapter_splitter.py -q`

Expected: PASS.

---

### Task 5: Add ChapterIntakeService and Artifact Trace

**Files:**
- Create: `backend/app/services/chapter_intake_service.py`
- Modify: `backend/app/domain/artifacts.py`
- Test: `backend/tests/services/test_chapter_intake_service.py`

- [ ] **Step 1: Add failing orchestration test**

```python
from app.ai.providers.fake_provider import FakeProvider
from app.services.chapter_intake_service import ChapterIntakeService


def test_auto_split_persists_three_chapters_and_split_artifact(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("XENGINEER_DATA_ROOT", str(tmp_path))
    service = ChapterIntakeService(provider=FakeProvider())

    chapters, trace = service.auto_split_and_save(
        "project_abc",
        "声明:仅供预览交流。\\n\\n雨夜里，林晚回家。\\n\\n电话响起。\\n\\n旧信出现。",
        mode="auto",
    )

    assert len(chapters) == 3
    assert trace["mode_used"] == "ai"
```

- [ ] **Step 2: Run test to verify failure**

Run: `pytest backend/tests/services/test_chapter_intake_service.py -q`

Expected: FAIL because service and artifact type do not exist.

- [ ] **Step 3: Add `chapter_split_plan` artifact type**

In `backend/app/domain/artifacts.py`:

```python
ArtifactType = Literal[
    "chapter_split_plan",
    "novel_analysis",
    "story_bible",
    "adaptation_plan",
    "screenplay_json",
    "screenplay_yaml",
    "screenplay_rendered",
    "audit_report",
]
```

- [ ] **Step 4: Create service**

```python
from __future__ import annotations

from typing import Any

from app.ai.providers.factory import build_ai_provider
from app.ai.skills.chapter_boundary_reader import ChapterBoundaryReaderSkill
from app.domain.source import Chapter
from app.services.artifact_service import ArtifactService
from app.services.chapter_service import ChapterService
from app.services.chapter_splitter import ChapterSplitter


class ChapterIntakeService:
    """章节导入编排：拆分 raw txt、保存章节、记录 AI boundary trace。"""

    def __init__(
        self,
        chapter_service: ChapterService | None = None,
        artifact_service: ArtifactService | None = None,
        provider: Any | None = None,
    ) -> None:
        self.chapter_service = chapter_service or ChapterService()
        self.artifact_service = artifact_service or ArtifactService()
        self.provider = provider or build_ai_provider()

    def auto_split_and_save(self, project_id: str, text: str, mode: str = "auto") -> tuple[list[Chapter], dict[str, Any]]:
        boundary_reader = ChapterBoundaryReaderSkill(self.provider)
        split_result = ChapterSplitter(boundary_reader=boundary_reader).split_with_trace(text, mode=mode)
        chapters = self.chapter_service.replace_for_project(
            project_id,
            [chapter.to_dict() for chapter in split_result.chapters],
        )
        trace = split_result.trace()
        if split_result.mode_used == "ai" or trace["ignored_spans"] or trace["warnings"]:
            self.artifact_service.save_artifact(project_id, "chapter_split_plan", trace)
        return chapters, trace
```

- [ ] **Step 5: Run service test**

Run: `pytest backend/tests/services/test_chapter_intake_service.py -q`

Expected: PASS.

---

### Task 6: Keep API Contract Stable

**Files:**
- Modify: `backend/app/api/routes_chapters.py`
- Test: `backend/tests/api/test_chapters_auto_split.py`

- [ ] **Step 1: Write API contract test**

```python
from fastapi.testclient import TestClient

from app.main import create_app


def test_auto_split_response_shape_stays_stable(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("XENGINEER_DATA_ROOT", str(tmp_path))
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"title": "拆章测试"}).json()

    response = client.post(
        f"/api/projects/{project['id']}/chapters/auto-split",
        json={
            "text": (
                "声明:仅供预览交流。\\n\\n"
                "第一章 雨夜归来\\n正文一。\\n\\n"
                "第二章 旧案重启\\n正文二。\\n\\n"
                "第三章 钟声之后\\n正文三。"
            )
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert set(payload.keys()) == {"chapters", "chapter_count", "mode_used"}
    assert payload["chapter_count"] == 3
    assert payload["chapters"][0]["title"] == "第一章 雨夜归来"
```

- [ ] **Step 2: Run test to verify failure**

Run: `pytest backend/tests/api/test_chapters_auto_split.py -q`

Expected: FAIL until route uses `ChapterIntakeService`.

- [ ] **Step 3: Replace route internals**

```python
from app.services.chapter_intake_service import ChapterIntakeService
```

In `auto_split_chapters`:

```python
chapters, trace = ChapterIntakeService().auto_split_and_save(project_id, request.text, request.mode)
return AutoSplitResponse(
    chapters=[{"title": chapter.title, "text": chapter.text} for chapter in chapters],
    chapter_count=len(chapters),
    mode_used=trace["mode_used"],
)
```

- [ ] **Step 4: Run API test**

Run: `pytest backend/tests/api/test_chapters_auto_split.py -q`

Expected: PASS.

---

### Task 7: Strengthen NovelReader Prompt Without Moving It Earlier

**Files:**
- Modify: `backend/app/ai/prompts/novel_reader.md`
- Test: `backend/tests/ai/test_ai_providers.py`

- [ ] **Step 1: Add prompt contract text**

Add sections:

```markdown
## Additional Extraction Duties

- Extract core conflicts, character candidates, relationship hints, and continuity anchors from the saved chapters.
- Treat chapter and paragraph IDs as source truth.
- Keep every extracted event and continuity anchor source-backed.
- Mark inferred facts with `evidence_level: inferred`.

## Boundary

- Do not split raw text.
- Do not clean copyright notices or catalogs.
- Do not create chapter IDs or paragraph IDs.
- Do not write screenplay scenes or dialogue.
```

- [ ] **Step 2: Run provider contract tests**

Run: `pytest backend/tests/ai/test_ai_providers.py -q`

Expected: PASS because prompt text changes should not alter fake provider behavior.

---

### Task 8: Update Docs and Manual Fixtures

**Files:**
- Modify: `fixtures/前端接入指南.md`
- Modify: `BACKEND_UNIMPLEMENTED_VERSION_MAP.md`
- Keep: `docs/specs/backend-ChapterSpliter-NovelReader/split-fixtures/**`

- [ ] **Step 1: Update frontend guide**

Add to auto-split section:

```markdown
`auto-split` 会自动忽略声明、广告、目录和序章，默认只保存正文第 1-3 章。响应形状不变；如果后端调用 AI boundary planner，调试 trace 会保存为 `chapter_split_plan` artifact。
```

- [ ] **Step 2: Update version map**

Change `ChapterSplitter._split_by_ai` row to:

```markdown
| `ChapterSplitter._split_by_ai` | 已有设计：规则不足 3 个可信正文章节时调用轻量 `ChapterBoundaryReaderSkill`，代码负责切片和 ID | V0 模块 A 增强项 | 阻塞“无章节标记长文自动拆章”的体验，不阻塞手动三章 demo | 按 `docs/specs/backend-ChapterSpliter-NovelReader/IMPLEMENTATION_PLAN.md` 实现 |
```

- [ ] **Step 3: Run focused test suite**

Run:

```powershell
pytest backend/tests/services/test_chapter_splitter.py backend/tests/services/test_chapter_intake_service.py backend/tests/ai/test_chapter_boundary_reader.py backend/tests/api/test_chapters_auto_split.py -q
```

Expected: PASS.

- [ ] **Step 4: Run smoke API test**

Run:

```powershell
pytest backend/tests/test_api_smoke_flow.py -q
```

Expected: PASS. Existing generation artifact count remains 7 unless the smoke test explicitly calls `auto-split`.

---

## Self-Review

Spec coverage:

- Failure definition is covered by Tasks 1, 2, 4 and `ACCEPTANCE.md`.
- Frontend contract stability is covered by Task 6.
- Reusing `.tmp-novel-to-script-team` is covered by `reference-reuse/novel-analyzer-split.md` and Task 7.
- Artifact trace is covered by Task 5.
- Manual inspection fixtures are under `split-fixtures/`.

Placeholder scan:

- No `TBD`, `TODO`, or unspecified “add tests” steps remain.

Type consistency:

- `ChapterBoundaryReaderSkill.skill_name == "chapter_boundary_reader"` is used consistently in fake provider and tests.
- `chapter_split_plan` is used consistently as artifact type.
- Public API response remains `AutoSplitResponse`.


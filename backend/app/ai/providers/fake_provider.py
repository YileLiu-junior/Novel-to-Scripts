from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Any

from app.ai.providers.base import AiProvider, StructuredGenerationRequest, StructuredGenerationResult


# FakeProvider 是开发联调用的确定性 provider。它可以读取项目级 fixture，
# 但没有匹配 fixture 时必须根据当前章节构造项目相关内容，避免把全局 demo
# 误展示成用户原文生成结果。


class FakeProvider(AiProvider):
    name = "fake"

    def __init__(self, fixtures: dict[str, dict[str, Any]] | None = None) -> None:
        self.fixtures = fixtures or {}

    def generate_structured(self, request: StructuredGenerationRequest) -> StructuredGenerationResult:
        payload = copy.deepcopy(self.fixtures.get(request.skill_name) or self._default_payload(request))
        return StructuredGenerationResult(
            provider=self.name,
            raw_output=None,
            parsed_output=payload,
        )

    def generate_text(self, prompt: str, temperature: float = 0.0, max_tokens: int | None = None) -> str:
        return "fake-provider-text-output"

    def _default_payload(self, request: StructuredGenerationRequest) -> dict[str, Any]:
        project = self._project_from_request(request)
        project_fixture = self._load_project_fixture(project, request.skill_name)
        if project_fixture is not None:
            return project_fixture

        chapters = self._chapters_from_request(request)
        if request.skill_name == "chapter_boundary_reader":
            return self._build_chapter_boundary_plan(request.input_data)
        if request.skill_name == "novel_reader":
            return self._build_novel_analysis(chapters)
        if request.skill_name == "story_ontology":
            return self._build_story_assets(request.input_data)
        if request.skill_name == "adaptation_planner":
            return self._build_adaptation_plan(request.input_data)
        if request.skill_name == "screenplay_writer":
            return self._build_screenplay_payload(request.input_data)
        return {}

    def _project_from_request(self, request: StructuredGenerationRequest) -> dict[str, Any]:
        project = request.input_data.get("project")
        return project if isinstance(project, dict) else {}

    def _chapters_from_request(self, request: StructuredGenerationRequest) -> list[dict[str, Any]]:
        direct = request.input_data.get("chapters")
        if isinstance(direct, list):
            return [item for item in direct if isinstance(item, dict)]
        nested = request.input_data.get("novel_analysis", {})
        if isinstance(nested, dict) and isinstance(nested.get("chapters"), list):
            return [item for item in nested["chapters"] if isinstance(item, dict)]
        chapters = request.input_data.get("chapters_used")
        if isinstance(chapters, list):
            return [item for item in chapters if isinstance(item, dict)]
        return []

    def _safe_project_name(self, project: dict[str, Any]) -> str | None:
        raw = project.get("title") or project.get("id")
        if not isinstance(raw, str) or not raw.strip():
            return None
        safe = re.sub(r'[\\/:*?"<>|]+', "_", raw.strip())
        safe = re.sub(r"\s+", "_", safe)
        return safe.strip("._ ") or None

    def _load_project_fixture(self, project: dict[str, Any], skill_name: str) -> dict[str, Any] | None:
        safe_name = self._safe_project_name(project)
        if not safe_name:
            return None
        filename_by_skill = {
            "novel_reader": "demo_story_bible.json",
            "story_ontology": "demo_story_bible.json",
            "adaptation_planner": "demo_screenplay.json",
            "screenplay_writer": "demo_screenplay.json",
        }
        filename = filename_by_skill.get(skill_name)
        if not filename:
            return None
        path = Path(__file__).resolve().parents[4] / "fixtures" / "projects" / safe_name / filename
        if not path.is_file():
            return None
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
        if skill_name == "adaptation_planner":
            return data.get("adaptation_plan", data)
        return data

    def _chapter_text(self, chapter: dict[str, Any]) -> str:
        text = chapter.get("text")
        if isinstance(text, str) and text.strip():
            return text.strip()
        paragraphs = chapter.get("paragraphs", [])
        if isinstance(paragraphs, list):
            parts = [p.get("text", "") for p in paragraphs if isinstance(p, dict) and p.get("text")]
            return "\n".join(parts).strip()
        return ""

    def _excerpt(self, text: str, limit: int = 120) -> str:
        compact = re.sub(r"\s+", " ", text).strip()
        return compact[:limit] if compact else "当前章节暂无正文。"

    def _build_chapter_boundary_plan(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """为 raw txt 自动拆章提供确定性边界计划，供前后端离线联调。"""
        lines = [item for item in input_data.get("line_index", []) if isinstance(item, dict)]
        target = input_data.get("target_main_chapters", 3)
        target_count = target if isinstance(target, int) and target > 0 else 3
        ignored = []
        story_lines = []
        heading_lines = []
        ignored_hints = ("声明", "txt02.com", "仅供预览", "版权", "下载", "本站")
        heading_pattern = re.compile(r"^第[零一二三四五六七八九十百千万\d]+[章节回卷部集]")
        for item in lines:
            text = str(item.get("text", ""))
            line_no = int(item.get("line", 0) or 0)
            stripped = text.strip()
            if not stripped:
                continue
            if any(hint in stripped for hint in ignored_hints):
                ignored.append(
                    {
                        "kind": "copyright_notice",
                        "start_line": line_no,
                        "end_line": line_no,
                        "reason": "fake provider detected non-story notice",
                    }
                )
            else:
                story_lines.append((line_no, stripped))
                if heading_pattern.match(stripped):
                    heading_lines.append((line_no, stripped))

        candidates = []
        if heading_lines:
            all_line_numbers = [line_no for line_no, _text in story_lines]
            max_line = max(all_line_numbers, default=0)
            for idx, (line_no, title) in enumerate(heading_lines[:target_count]):
                next_heading_line = heading_lines[idx + 1][0] if idx + 1 < len(heading_lines) else max_line + 1
                end_line = next_heading_line - 1
                candidates.append(
                    {
                        "chapter_kind": "main_chapter",
                        "title": title,
                        "start_line": line_no,
                        "end_line": end_line,
                        "confidence": 0.9,
                    }
                )
        else:
            for line_no, _text in story_lines[:target_count]:
                candidates.append(
                    {
                        "chapter_kind": "main_chapter",
                        "title": "",
                        "start_line": line_no,
                        "end_line": line_no,
                        "confidence": 0.8,
                    }
                )
        warnings = []
        if len(candidates) < target_count:
            warnings.append(
                {
                    "code": "chapters.too_few_after_ai_split",
                    "message": "fake provider found fewer than target main chapters",
                }
            )
        return {"ignored_spans": ignored, "candidate_chapters": candidates, "warnings": warnings}

    def _build_novel_analysis(self, chapters: list[dict[str, Any]]) -> dict[str, Any]:
        events = []
        for idx, chapter in enumerate(chapters[:3], start=1):
            text = self._chapter_text(chapter)
            chapter_id = chapter.get("id") or f"chapter_{idx:03d}"
            events.append(
                {
                    "id": f"event_{idx:03d}",
                    "title": chapter.get("title") or f"第 {idx} 章事件",
                    "summary": self._excerpt(text),
                    "event_type": "narrative",
                    "participants": ["char_001"],
                    "chapter_refs": [{"chapter_id": chapter_id}],
                    "source_refs": [{"chapter_id": chapter_id}],
                }
            )
        return {
            "provider_notice": "fake provider generated from current project chapters",
            "chapters": chapters,
            "events": events,
            "character_candidates": [
                {
                    "id": "char_001",
                    "name": "当前项目主角",
                    "source_refs": [{"chapter_id": chapters[0].get("id", "chapter_001")}] if chapters else [],
                }
            ],
            "locations": ["原文场景"],
            "objects": [],
            "foreshadowing_candidates": [],
        }

    def _build_story_assets(self, novel_analysis: dict[str, Any]) -> dict[str, Any]:
        chapters = self._chapters_from_request(StructuredGenerationRequest(
            skill_name="story_ontology",
            prompt_name="story_ontology.md",
            input_data={"novel_analysis": novel_analysis},
        ))
        first_chapter_id = chapters[0].get("id", "chapter_001") if chapters else "chapter_001"
        events = novel_analysis.get("events", []) if isinstance(novel_analysis.get("events"), list) else []
        if not events:
            events = self._build_novel_analysis(chapters).get("events", [])
        mode = self._adaptation_evidence_mode(novel_analysis)
        enriched_events = [self._enrich_event(event, idx, chapters) for idx, event in enumerate(events, start=1)]
        story_bible = {
            "characters": [
                {
                    "id": "char_001",
                    "name": "当前项目主角",
                    "aliases": [],
                    "narrative_role": "protagonist",
                    "voice_profile": {
                        "rhythm": "由上传原文的句式节奏模拟",
                        "diction": "保留原文章节中的关键词和语气",
                    },
                    "source_refs": [{"chapter_id": first_chapter_id}],
                }
            ],
            "relationship_edges": [],
            "knowledge_states": [{"character_id": "char_001", "knows": ["event_001"], "does_not_know": []}],
        }
        payload = {
            "story_bible": story_bible,
            "events": enriched_events if mode == "enabled" else events,
            "causal_graph": {
                "edges": [
                    {
                        "from": events[idx]["id"],
                        "to": events[idx + 1]["id"],
                        "relation": "leads_to",
                        "explanation": "fake provider 按上传章节顺序建立事件推进关系。",
                    }
                    for idx in range(max(0, len(events) - 1))
                ]
            },
            "foreshadowing": [
                {
                    "id": "foreshadow_001",
                    "description": "fake provider generated：根据当前原文保留待人工复核的伏笔位。",
                    "setup_event_id": events[0]["id"] if events else "event_001",
                    "status": "open",
                    "source_refs": [{"chapter_id": first_chapter_id}],
                }
            ],
            "chapters_used": chapters,
        }
        if mode == "minimal":
            return payload
        story_bible["continuity_anchors"] = [
            {
                "id": "anchor_001",
                "anchor_type": "timeline",
                "summary": "Fake Provider 保留当前项目前三章的原始顺序，避免后续场景解释脱离上传章节。",
                "applies_to": ["char_001"],
                "source_refs": [{"chapter_id": first_chapter_id}],
            }
        ]
        story_bible["dramatic_assets"] = {
            "conflict_pool": [
                {
                    "id": "conflict_001",
                    "conflict_axis": enriched_events[0].get("conflict_axis", "当前章节目标 vs 眼前阻碍")
                    if enriched_events
                    else "当前章节目标 vs 眼前阻碍",
                    "participants": ["char_001"],
                    "related_events": [event.get("id") for event in enriched_events[:2] if event.get("id")],
                    "source_refs": [{"chapter_id": first_chapter_id}],
                }
            ],
            "filmic_constraints": [
                {
                    "id": "filmic_001",
                    "constraint_type": "source_summary_to_action",
                    "summary": "章节摘要只能作为证据，后续剧本需要把它转成可演、可见、可听的行动。",
                    "related_characters": ["char_001"],
                    "related_events": [enriched_events[0]["id"]] if enriched_events else [],
                    "source_refs": [{"chapter_id": first_chapter_id}],
                }
            ],
        }
        return {
            "schema_version": "story_ontology_evidence_1.5",
            "adaptation_evidence_mode": mode,
            "generated_by_skill": "story_ontology",
            "input_artifact_type": "novel_analysis",
            **payload,
        }

    def _adaptation_evidence_mode(self, input_data: dict[str, Any]) -> str:
        """读取后端调试模式；缺失或非法值都回到用户默认的 enabled。"""
        config = input_data.get("adaptation_config")
        if isinstance(config, dict) and config.get("adaptation_evidence_mode") == "minimal":
            return "minimal"
        return "enabled"

    def _enrich_event(self, event: dict[str, Any], idx: int, chapters: list[dict[str, Any]]) -> dict[str, Any]:
        """为 fake StoryOntology 事件补上可审查证据字段，不创造改编决策。"""
        enriched = copy.deepcopy(event)
        chapter = chapters[min(idx - 1, len(chapters) - 1)] if chapters else {}
        chapter_id = chapter.get("id") or f"chapter_{idx:03d}"
        title = enriched.get("title") or f"事件 {idx}"
        summary = enriched.get("summary") or title
        enriched.setdefault("source_refs", [{"chapter_id": chapter_id}])
        enriched["complete_event"] = True
        enriched["event_flow"] = [
            f"进入《{chapter.get('title') or title}》",
            "提取原文行动",
            "形成章节结果",
        ]
        enriched["must_keep_together"] = True
        enriched["conflict_axis"] = f"{summary[:24]} vs 后续改编压缩"
        return enriched

    def _build_adaptation_plan(self, input_data: dict[str, Any]) -> dict[str, Any]:
        events = input_data.get("events", []) if isinstance(input_data.get("events"), list) else []
        retained = [event.get("id") for event in events if event.get("id")]
        return {
            "retained_events": retained,
            "merged_events": [],
            "deleted_or_deferred_events": [],
            "protected_elements": retained[:1],
            "scene_plan": [
                {
                    "scene_id": f"scene_{idx:03d}",
                    "purpose": event.get("summary") or event.get("title") or "承接当前章节内容",
                    "source_events": [event.get("id")],
                }
                for idx, event in enumerate(events[:3], start=1)
            ],
        }

    def _build_screenplay_payload(self, input_data: dict[str, Any]) -> dict[str, Any]:
        story_bible = input_data.get("story_bible", {}) if isinstance(input_data.get("story_bible"), dict) else {}
        events = input_data.get("events", []) if isinstance(input_data.get("events"), list) else []
        chapters = input_data.get("chapters_used", []) if isinstance(input_data.get("chapters_used"), list) else []
        if not chapters:
            chapters = [{"id": "chapter_001", "title": "当前项目章节", "text": "fake provider generated"}]
        scenes = []
        for idx, chapter in enumerate(chapters[:3], start=1):
            chapter_id = chapter.get("id") or f"chapter_{idx:03d}"
            title = chapter.get("title") or f"第 {idx} 章"
            text = self._chapter_text(chapter)
            excerpt = self._excerpt(text, 160)
            event_id = events[idx - 1].get("id") if idx - 1 < len(events) and events[idx - 1].get("id") else f"event_{idx:03d}"
            scenes.append(
                {
                    "id": f"scene_{idx:03d}",
                    "title": f"{title}：模拟改编场景",
                    "scene_heading": {
                        "sequence": idx,
                        "location": title,
                        "interior_exterior": "INT",
                        "time_of_day": "day",
                        "text": f"{idx}. {title} 内景 日",
                    },
                    "source_refs": [{"chapter_id": chapter_id}],
                    "dramatic_purpose": [f"验证当前项目章节《{title}》已进入生成链路。"],
                    "location": {"name": title, "time": "day", "interior_exterior": "INT"},
                    "characters": ["char_001"],
                    "related_events": [event_id],
                    "action": [f"【Fake Provider】根据《{title}》构造：{excerpt}"],
                    "content_blocks": [
                        {
                            "id": f"block_{idx:03d}",
                            "block_type": "action",
                            "text": f"【Fake Provider】根据《{title}》构造：{excerpt}",
                        }
                    ],
                    "dialogue": [
                        {
                            "id": f"line_{idx:03d}",
                            "character_id": "char_001",
                            "line": f"这一场来自《{title}》，不是全局 demo fixture。",
                            "surface_intent": "说明当前场景来源",
                            "subtext": "提示用户当前处于 fake provider 模式",
                            "emotional_state": "clear",
                            "action_hint": "指向章节标题",
                        }
                    ],
                }
            )
        return {
            "story_bible": story_bible,
            "events": events,
            "causal_graph": input_data.get("causal_graph", {"edges": []}),
            "foreshadowing": input_data.get("foreshadowing", []),
            "adaptation_plan": input_data.get("adaptation_plan", {}),
            "scenes": scenes,
            "script_structure": {
                "story_synopsis": "Fake Provider 根据当前上传章节生成的联调梗概：" + "；".join(
                    chapter.get("title", "") for chapter in chapters[:3]
                ),
                "story_outline": [
                    {
                        "id": f"outline_{idx:03d}",
                        "summary": scene["action"][0],
                        "related_events": scene["related_events"],
                        "target_scenes": [scene["id"]],
                    }
                    for idx, scene in enumerate(scenes, start=1)
                ],
                "literary_screenplay": {
                    "unit": "scene",
                    "format_note": "fake provider generated from current project chapters",
                    "scene_ids": [scene["id"] for scene in scenes],
                },
            },
            "audit_report": {
                "schema_warnings": [],
                "continuity_warnings": [],
                "dialogue_warnings": [
                    {
                        "id": "warning_001",
                        "severity": "info",
                        "type": "dialogue",
                        "message": "Fake Provider 模式：当前内容为项目相关模拟结果。",
                        "target": {"scene_id": "scene_001"},
                        "needs_human_review": False,
                    }
                ],
                "unresolved_foreshadowing": [],
            },
        }

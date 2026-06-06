from __future__ import annotations

from typing import Any

from app.domain.common import ValidationFinding

# 这个类负责验证剧本中的引用关系是否正确，比如场景中引用的章节、角色、事件是否存在，以及因果图中的事件引用是否存在等。它会返回一个包含所有验证结果的列表，前端可以根据这些结果向用户展示相应的错误或警告信息。
class ReferenceValidator:
    def validate_screenplay(self, screenplay: dict[str, Any]) -> list[ValidationFinding]:
        chapters = {item["id"] for item in screenplay.get("source", {}).get("chapters", [])}
        characters = {item["id"] for item in screenplay.get("story_bible", {}).get("characters", [])}
        relationships = {item["id"] for item in screenplay.get("story_bible", {}).get("relationship_edges", [])}
        events = {item["id"] for item in screenplay.get("events", [])}
        scenes = {item["id"] for item in screenplay.get("scenes", [])}
        findings: list[ValidationFinding] = []

        for scene in screenplay.get("scenes", []):
            scene_id = scene.get("id")
            scene_characters = set(scene.get("characters", []))
            scene_dialogue_lines = {line.get("id") for line in scene.get("dialogue", []) if isinstance(line, dict)}
            for ref in scene.get("source_refs", []):
                chapter_id = ref.get("chapter_id")
                if chapter_id not in chapters:
                    findings.append(
                        self._finding(
                            "reference.missing_chapter",
                            "error",
                            f"Scene {scene_id} references missing chapter {chapter_id}.",
                            "scene",
                            scene_id,
                        )
                    )
            for character_id in scene_characters:
                if character_id not in characters:
                    findings.append(
                        self._finding(
                            "reference.missing_character",
                            "error",
                            f"Scene {scene_id} references missing character {character_id}.",
                            "scene",
                            scene_id,
                        )
                    )
            for event_id in scene.get("related_events", []):
                if event_id not in events:
                    findings.append(
                        self._finding(
                            "reference.missing_event",
                            "warning",
                            f"Scene {scene_id} references missing event {event_id}.",
                            "scene",
                            scene_id,
                        )
                    )
            for line in scene.get("dialogue", []):
                character_id = line.get("character_id")
                if character_id not in scene_characters:
                    findings.append(
                        self._finding(
                            "reference.dialogue_character_not_in_scene",
                            "error",
                            f"Dialogue {line.get('id')} uses character {character_id}, which is not in scene {scene_id}.",
                            "dialogue",
                            line.get("id"),
                        )
                    )
            # content_blocks 是文学剧本自然段正文；如果它引用角色或台词，也要和 scene 内结构对齐。
            for block in scene.get("content_blocks", []):
                character_id = block.get("character_id")
                if character_id and character_id not in scene_characters:
                    findings.append(
                        self._finding(
                            "reference.content_block_character_not_in_scene",
                            "error",
                            f"Content block {block.get('id')} uses character {character_id}, which is not in scene {scene_id}.",
                            "content_block",
                            block.get("id"),
                        )
                    )
                dialogue_line_id = block.get("dialogue_line_id")
                if dialogue_line_id and dialogue_line_id not in scene_dialogue_lines:
                    findings.append(
                        self._finding(
                            "reference.content_block_dialogue_missing",
                            "warning",
                            f"Content block {block.get('id')} references missing dialogue line {dialogue_line_id}.",
                            "content_block",
                            block.get("id"),
                        )
                    )

        for edge in screenplay.get("causal_graph", {}).get("edges", []):
            for key in ("from", "to"):
                event_id = edge.get(key)
                if event_id not in events:
                    findings.append(
                        self._finding(
                            "reference.causal_event_missing",
                            "warning",
                            f"Causal edge references missing event {event_id}.",
                            "event",
                            event_id,
                        )
                    )

        for item in screenplay.get("foreshadowing", []):
            setup_event_id = item.get("setup_event_id")
            if setup_event_id not in events:
                findings.append(
                    self._finding(
                        "reference.foreshadowing_setup_missing",
                        "warning",
                        f"Foreshadowing {item.get('id')} references missing setup event {setup_event_id}.",
                        "foreshadowing",
                        item.get("id"),
                    )
                )
            payoff_scene_id = item.get("payoff_scene_id")
            if payoff_scene_id and payoff_scene_id not in scenes:
                findings.append(
                    self._finding(
                        "reference.foreshadowing_payoff_scene_missing",
                        "warning",
                        f"Foreshadowing {item.get('id')} references missing payoff scene {payoff_scene_id}.",
                        "foreshadowing",
                        item.get("id"),
                    )
                )
        # 新增结构层只保存索引和解释，不承载正文；这里检查它们是否指向真实实体。
        script_structure = screenplay.get("script_structure", {})
        for outline in script_structure.get("story_outline", []):
            for event_id in outline.get("related_events", []):
                if event_id not in events:
                    findings.append(
                        self._finding(
                            "reference.outline_event_missing",
                            "warning",
                            f"Outline {outline.get('id')} references missing event {event_id}.",
                            "outline",
                            outline.get("id"),
                        )
                    )
            for target_scene_id in outline.get("target_scenes", []):
                if target_scene_id not in scenes:
                    findings.append(
                        self._finding(
                            "reference.outline_scene_missing",
                            "warning",
                            f"Outline {outline.get('id')} references missing scene {target_scene_id}.",
                            "outline",
                            outline.get("id"),
                        )
                    )

        literary_screenplay = script_structure.get("literary_screenplay", {})
        for scene_id in literary_screenplay.get("scene_ids", []):
            if scene_id not in scenes:
                findings.append(
                    self._finding(
                        "reference.literary_screenplay_scene_missing",
                        "warning",
                        f"Literary screenplay references missing scene {scene_id}.",
                        "script_structure",
                        "literary_screenplay",
                    )
                )

        core_elements = screenplay.get("core_elements", {})
        for character_id in core_elements.get("protagonists", []):
            if character_id not in characters:
                findings.append(
                    self._finding(
                        "reference.protagonist_missing",
                        "error",
                        f"Core elements reference missing protagonist {character_id}.",
                        "character",
                        character_id,
                    )
                )
        for relationship_id in core_elements.get("character_relationships", []):
            if relationship_id not in relationships:
                findings.append(
                    self._finding(
                        "reference.relationship_missing",
                        "warning",
                        f"Core elements reference missing relationship {relationship_id}.",
                        "relationship",
                        relationship_id,
                    )
                )
        for action in core_elements.get("actions", []):
            scene_id = action.get("scene_id")
            if scene_id not in scenes:
                findings.append(
                    self._finding(
                        "reference.core_action_scene_missing",
                        "warning",
                        f"Core action {action.get('id')} references missing scene {scene_id}.",
                        "action",
                        action.get("id"),
                    )
                )
            event_id = action.get("related_event_id")
            if event_id and event_id not in events:
                findings.append(
                    self._finding(
                        "reference.core_action_event_missing",
                        "warning",
                        f"Core action {action.get('id')} references missing event {event_id}.",
                        "action",
                        action.get("id"),
                    )
                )
        for plot_item in core_elements.get("plot", []):
            event_id = plot_item.get("event_id")
            if event_id not in events:
                findings.append(
                    self._finding(
                        "reference.plot_event_missing",
                        "warning",
                        f"Plot item references missing event {event_id}.",
                        "event",
                        event_id,
                    )
                )
        for situation in core_elements.get("situations", []):
            scene_id = situation.get("scene_id")
            if scene_id not in scenes:
                findings.append(
                    self._finding(
                        "reference.situation_scene_missing",
                        "warning",
                        f"Situation {situation.get('id')} references missing scene {scene_id}.",
                        "situation",
                        situation.get("id"),
                    )
                )
        return findings

    def _finding(
        self,
        code: str,
        severity: str,
        message: str,
        target_type: str | None,
        target_id: str | None,
    ) -> ValidationFinding:
        return ValidationFinding(
            code=code,
            severity=severity,  # type: ignore[arg-type]
            message=message,
            target_type=target_type,
            target_id=target_id,
        )

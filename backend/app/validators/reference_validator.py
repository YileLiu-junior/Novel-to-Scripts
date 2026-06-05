from __future__ import annotations

from typing import Any

from app.domain.common import ValidationFinding


class ReferenceValidator:
    def validate_screenplay(self, screenplay: dict[str, Any]) -> list[ValidationFinding]:
        chapters = {item["id"] for item in screenplay.get("source", {}).get("chapters", [])}
        characters = {item["id"] for item in screenplay.get("story_bible", {}).get("characters", [])}
        events = {item["id"] for item in screenplay.get("events", [])}
        scenes = {item["id"] for item in screenplay.get("scenes", [])}
        findings: list[ValidationFinding] = []

        for scene in screenplay.get("scenes", []):
            scene_id = scene.get("id")
            scene_characters = set(scene.get("characters", []))
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


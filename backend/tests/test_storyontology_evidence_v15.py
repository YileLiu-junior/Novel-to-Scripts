from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

from app.domain.adaptation import AdaptationConfig
from app.domain.story_bible import Event, StoryBible
from app.validators.reference_validator import ReferenceValidator


ROOT = Path(__file__).resolve().parents[2]


def _load_fixture(name: str) -> dict:
    return json.loads((ROOT / "fixtures" / name).read_text(encoding="utf-8"))


def test_adaptation_config_defaults_to_enabled_evidence_mode() -> None:
    config = AdaptationConfig()

    assert config.adaptation_evidence_mode == "enabled"
    assert config.model_dump()["adaptation_evidence_mode"] == "enabled"


def test_domain_models_parse_enriched_and_legacy_story_bible_shapes() -> None:
    enriched = _load_fixture("demo_story_bible.json")
    bible = StoryBible.model_validate(enriched["story_bible"])
    event = Event.model_validate(enriched["events"][0])

    assert bible.continuity_anchors
    assert bible.dramatic_assets.conflict_pool
    assert event.complete_event is True
    assert event.must_keep_together is True

    legacy = {
        "characters": [{"id": "char_001", "name": "旧角色"}],
        "relationship_edges": [],
        "knowledge_states": [],
    }
    legacy_bible = StoryBible.model_validate(legacy)

    assert legacy_bible.continuity_anchors == []
    assert legacy_bible.dramatic_assets.conflict_pool == []


def test_enriched_screenplay_fixture_passes_schema_validation() -> None:
    schema = _load_fixture("../schemas/screenplay.schema.json")
    fixture = _load_fixture("demo_screenplay.json")

    errors = list(Draft202012Validator(schema).iter_errors(fixture))

    assert errors == []



def test_reference_validator_reports_storyontology_evidence_broken_refs() -> None:
    screenplay = _load_fixture("demo_screenplay.json")
    screenplay["story_bible"]["continuity_anchors"][0]["applies_to"].append("char_999")
    screenplay["story_bible"]["continuity_anchors"][0]["source_refs"] = [{"chapter_id": "chapter_999"}]
    screenplay["story_bible"]["dramatic_assets"]["conflict_pool"][0]["related_events"].append("event_999")
    screenplay["story_bible"]["dramatic_assets"]["filmic_constraints"][0]["related_characters"].append("char_999")

    findings = ReferenceValidator().validate_screenplay(screenplay)
    codes = {finding.code for finding in findings}
    targets = {finding.target_id for finding in findings}

    assert "reference.evidence_anchor_character_missing" in codes
    assert "reference.evidence_anchor_chapter_missing" in codes
    assert "reference.evidence_conflict_event_missing" in codes
    assert "reference.evidence_filmic_character_missing" in codes
    assert "char_999" in targets
    assert "event_999" in targets


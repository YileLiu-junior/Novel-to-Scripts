# S1 Fixture Contract

## Owner

Contract Architect.

## Purpose

Lock the shared language before domain, API, prompts, or frontend code move.
Fixtures are the first source of agreement between backend, frontend, tests,
and skills.

## Files

- `fixtures/demo_novel_3_chapters.json`
- `fixtures/demo_story_bible.json`
- `fixtures/demo_screenplay.json`
- `fixtures/demo_screenplay.yaml`
- `fixtures/demo_audit_report.json`
- `fixtures/demo_invalid_refs.yaml`

## Contract

- JSON/Pydantic is the internal source of truth.
- YAML is an export and user-editable interchange format.
- IDs in fixtures must look like final backend IDs:
  - `chapter_###`
  - `p_###`
  - `char_###`
  - `event_###`
  - `scene_###`
  - `line_###`
  - `warning_###`
- `demo_novel_3_chapters.json` must include at least three chapters.
- Demo story bible must include at least two characters, three events, one
  relationship, one foreshadowing item, and knowledge-state examples.
- Demo screenplay must include at least two scenes and source references.
- Invalid refs fixture must contain at least one broken `character_id` or
  `event_id`.

## Review Gate

Gate 1 Contract passes only when fixture changes are reflected in schema,
domain models, DTOs, and prompt reference examples.


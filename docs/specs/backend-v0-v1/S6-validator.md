# S6 Validator

## Owner

Validation Director.

## Purpose

Give structural trust to deterministic code instead of asking the model to
judge its own output.

## Files

- `backend/app/validators/chapter_validator.py`
- `backend/app/validators/schema_validator.py`
- `backend/app/validators/reference_validator.py`
- `backend/app/validators/audit_validator.py`
- `backend/app/services/validation_service.py`

## Rules

- Validators do not call models.
- Validators do not call network APIs.
- Validators should be testable with fixtures alone.
- Schema validation checks shape.
- Reference validation checks cross-entity integrity.
- Audit validation maps findings into user-visible warnings.

## Minimal Checks

- `source_refs.chapter_id` exists.
- `scene.characters[]` exist in `story_bible.characters`.
- `dialogue.character_id` belongs to current scene characters.
- `related_events[]` exist in `events`.
- `causal_graph.edges.from/to` exist in `events`.
- `foreshadowing.setup_event_id` exists.
- `foreshadowing.payoff_scene_id`, when set, exists in `scenes`.

## Acceptance

- Missing character references return an error.
- Missing event references return a warning or error according to severity.
- `fixtures/demo_invalid_refs.yaml` triggers expected findings.


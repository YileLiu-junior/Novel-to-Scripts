# Screenplay Schema Design

## Design Goal

The schema describes an adaptation asset, not just screenplay formatting. It
keeps source references, story bible, adaptation decisions, scene text, and
audit warnings in one inspectable structure.

## Canonical Source

`schemas/screenplay.schema.json` is the canonical machine-readable schema.
`schemas/screenplay.schema.yaml` mirrors the design for humans and docs.

## Why The Schema Includes Story Bible

V0+V1 keeps a minimal story bible so later steps can refer to stable
characters, relationships, events, and foreshadowing. Without this layer,
`adaptation_plan` would be a prompt-only explanation with no stable references.

## Why JSON Is Internal And YAML Is External

The backend should validate and persist JSON/Pydantic structures. YAML is for
human review, editing, demo, and export. User-edited YAML must be parsed back to
JSON before validation.

## What Schema Does Not Do

Schema does not prove that `char_001` exists in a scene, or that
`event_003` exists in the causal graph. Those are cross-reference checks and
belong in `backend/app/validators/reference_validator.py`.

## Required Future Compatibility

The schema reserves lightweight fields for:

- richer story bible in V2,
- causal graph and foreshadowing in V3,
- dialogue subtext in V4,
- audit loops in V5.

These fields should be extended, not replaced.


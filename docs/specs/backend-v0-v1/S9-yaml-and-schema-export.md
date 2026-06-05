# S9 YAML And Schema Export

## Owner

Backend Builder with Validation Director.

## Purpose

Produce visible, reviewable competition/demo assets while keeping internal
truth in JSON/Pydantic.

## Files

- `backend/app/exporters/yaml_exporter.py`
- `backend/app/exporters/schema_exporter.py`
- `backend/app/services/yaml_service.py`
- `backend/app/services/schema_service.py`
- `schemas/screenplay.schema.json`
- `schemas/screenplay.schema.yaml`
- `docs/schema/screenplay-schema-explained.md`

## Rules

- Exporters serialize already-validated structures.
- Exporters do not fill missing fields.
- Exporters do not repair model output.
- User-edited YAML is parsed back into JSON before validation.

## Acceptance

- YAML export can parse back to JSON.
- YAML validation returns findings.
- Download without `screenplay_json` returns a clear error.


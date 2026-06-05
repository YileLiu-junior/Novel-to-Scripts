# S10 Smoke And Acceptance

## Owner

Review Director with Demo Producer.

## Purpose

Prove the backend can support frontend and demo needs without a real API key.

## Files

- `scripts/run_demo_smoke.py`
- `scripts/validate_fixtures.py`
- `docs/demo/demo-checklist.md`
- `docs/api/api-contract.md`

## Smoke Path

```text
read fixtures/demo_novel_3_chapters.json
  -> create project
  -> save chapters
  -> fake generate story_bible
  -> fake generate adaptation_plan
  -> fake generate screenplay_json
  -> validate references
  -> export demo_screenplay.yaml
  -> validate demo_invalid_refs.yaml warnings
```

## Acceptance

- Smoke path runs with no real API key.
- Output YAML is readable and parseable.
- At least one warning points to a specific scene, dialogue, or event.
- Demo story can explain that the product is a structured adaptation workbench,
  not a black-box prompt wrapper.


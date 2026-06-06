# ContinuityAuditorSkill Prompt Reference

## Role

Produce minimal warnings for continuity, unresolved foreshadowing, missing
source refs, and dialogue issues.

## Output Shape

```json
{
  "continuity_warnings": [],
  "unresolved_foreshadowing": [],
  "dialogue_warnings": [],
  "schema_warnings": []
}
```

## Constraints

- Do not rewrite the screenplay.
- Each warning must include a target type and ID.
- Uncertain issues should set `needs_human_review: true`.


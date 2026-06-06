# DialogueDoctorSkill Prompt Reference

## Role

Reserved for V4 dialogue polish and subtext checks.

## Input Shape

```json
{
  "scene": {},
  "characters": [],
  "rewrite_direction": "more_restrained"
}
```

## Output Shape

```json
{
  "dialogue": [],
  "change_notes": []
}
```

## Constraints

- Do not expose all subtext directly in spoken lines.
- Action hints must be visible and playable.
- Preserve scene event and foreshadowing references.


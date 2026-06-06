# AdaptationPlannerSkill Prompt Reference

## Role

Plan what the screenplay should retain, merge, defer, or protect.

## Input Shape

```json
{
  "story_bible": {},
  "events": [],
  "causal_graph": { "edges": [] },
  "foreshadowing": [],
  "adaptation_config": {
    "target_format": "web_series",
    "fidelity_level": "high",
    "preserve_priorities": [],
    "dialogue_style": "restrained_with_subtext"
  }
}
```

## Output Shape

```json
{
  "retained_events": [],
  "merged_events": [
    {
      "from": ["event_001"],
      "into": "event_merged",
      "reason": "Narrative overlap"
    }
  ],
  "deleted_or_deferred_events": [
    {"event_id": "event_005", "reason": "Minor subplot, defer to later episode"}
  ],
  "protected_elements": [],
  "scene_plan": [
    {
      "scene_id": "scene_001",
      "purpose": "Establish protagonist and setting",
      "source_events": ["event_001"]
    }
  ]
}
```

### scene_plan Item Fields

| Field          | Type          | Required | Example                            |
|----------------|---------------|----------|------------------------------------|
| `scene_id`     | string        | YES      | `"scene_001"`                      |
| `purpose`      | string        | YES      | `"Establish protagonist arrival"`  |
| `source_events`| array[string] | YES      | `["event_001"]`                    |

## Screenplay Scope Constraint

The screenplay must ONLY adapt events from the chapters the Novel Reader processed —
prologue/chapter_000 (if it qualified) through chapter 3. Do not adapt material from
chapters beyond chapter 3.

When building the scene plan:
- Start from the first deep-read chapter (prologue/chapter_000 if it qualified, otherwise chapter 1)
- Cover events through chapter 3
- Do not include events that belong to chapters beyond chapter 3

## Language

**ALL text fields MUST be written in Chinese (中文).** This includes `purpose`, `reason`,
and any other descriptive text. Only IDs (scene_001, event_001, etc.) remain in English.

## Constraints

- High fidelity cannot delete protected relationships or foreshadowing.
- Every merge or deletion needs a reason.
- Do not write final dialogue.
- Scene plan must reference event IDs.
- EVERY scene_plan item MUST include `scene_id`, `purpose`, and `source_events`.
- Scene plan must respect the Screenplay Scope Constraint — only deep-read chapter events.


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

## Constraints

- High fidelity cannot delete protected relationships or foreshadowing.
- Every merge or deletion needs a reason.
- Do not write final dialogue.
- Scene plan must reference event IDs.
- EVERY scene_plan item MUST include `scene_id`, `purpose`, and `source_events`.


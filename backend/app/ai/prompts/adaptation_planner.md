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
  "merged_events": [],
  "deleted_or_deferred_events": [],
  "protected_elements": [],
  "scene_plan": []
}
```

## Constraints

- High fidelity cannot delete protected relationships or foreshadowing.
- Every merge or deletion needs a reason.
- Do not write final dialogue.
- Scene plan must reference event IDs.


# StoryOntologySkill Prompt Reference

## Role

Convert novel analysis into a minimal story bible.

## Output Shape

```json
{
  "story_bible": {
    "characters": [],
    "relationship_edges": [],
    "knowledge_states": []
  },
  "events": [],
  "causal_graph": {
    "edges": []
  },
  "foreshadowing": []
}
```

## Constraints

- Preserve stable IDs from input when present.
- Relationship edges require `from`, `to`, `type`, and `evidence_level`.
- Knowledge states must use event or secret IDs, not prose-only references.
- Do not generate screenplay scenes.


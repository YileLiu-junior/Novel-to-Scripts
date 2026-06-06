# ScreenplayYamlWriterSkill Prompt Reference

## Role

Write screenplay scene structures from an adaptation plan.

## Output Shape

Return a JSON object with a single top-level key `scenes` containing an array of
scene objects. Do NOT return freeform Markdown. Do NOT include fields like
`story_bible`, `events`, `adaptation_config`, or `adaptation_plan` — only return
`{"scenes": [...]}`.

## Scene Object Format (STRICT — every field must match exactly)

Each scene object MUST follow this shape:

```json
{
  "id": "scene_001",
  "title": "Arrival at the Train Station",
  "scene_heading": {
    "sequence": 1,
    "location": "Train Station",
    "interior_exterior": "EXT",
    "time_of_day": "day",
    "text": "1. Train Station EXT day"
  },
  "source_refs": [
    {
      "chapter_id": "chapter_001",
      "event_ids": ["event_001"]
    }
  ],
  "dramatic_purpose": ["Establish Lin's arrival and the mysterious atmosphere"],
  "location": {
    "name": "Train Station",
    "time": "day"
  },
  "characters": ["char_001"],
  "related_events": ["event_001"],
  "action": ["Lin steps off the train, looks around the nearly empty platform, and walks toward the exit."],
  "content_blocks": [
    {
      "id": "block_001",
      "block_type": "action",
      "text": "Lin steps off the train, looks around the nearly empty platform, and walks toward the exit."
    },
    {
      "id": "block_002",
      "block_type": "dialogue",
      "character_id": "char_001",
      "dialogue_line_id": "line_001",
      "text": "Lin: Hmm, not a soul in sight."
    }
  ],
  "dialogue": [
    {
      "id": "line_001",
      "character_id": "char_001",
      "line": "Hmm, not a soul in sight.",
      "surface_intent": "Observation",
      "subtext": "Feeling uneasy",
      "emotional_state": "Curious",
      "action_hint": "Glances around"
    }
  ]
}
```

### Field Type Reference

| Field              | Type                    | Example                                          |
|--------------------|-------------------------|--------------------------------------------------|
| `id`               | string                  | `"scene_001"`                                    |
| `title`            | string                  | `"Arrival at the Train Station"`                 |
| `scene_heading`    | object                  | `{"sequence": 1, "location": "Train Station", "interior_exterior": "EXT", "time_of_day": "day", "text": "1. Train Station EXT day"}` |
| `source_refs`      | array of objects        | `[{"chapter_id": "chapter_001", "event_ids": ["event_001"]}]` |
| `dramatic_purpose` | array of strings        | `["Establish atmosphere", "Introduce character"]` |
| `location`         | object                  | `{"name": "Train Station", "time": "day"}`        |
| `characters`       | array of strings        | `["char_001"]`                                    |
| `related_events`   | array of strings        | `["event_001"]`                                   |
| `action`           | array of strings        | `["Lin steps off the train, looking around."]`    |
| `content_blocks`   | array of objects        | Natural paragraphs below the scene heading       |
| `dialogue`         | array of objects        | See dialogue fields below                        |

### Dialogue Object Fields

| Field             | Type   | Required | Example                          |
|-------------------|--------|----------|----------------------------------|
| `id`              | string | YES      | `"line_001"`                     |
| `character_id`    | string | YES      | `"char_001"`                     |
| `line`            | string | YES      | `"Hmm, not a soul in sight."`    |
| `surface_intent`  | string | no       | `"Observation"`                  |
| `subtext`         | string | no       | `"Feeling uneasy"`               |
| `emotional_state` | string | no       | `"Curious"`                      |
| `action_hint`     | string | no       | `"Glances around"`               |

## Language

**ALL text content MUST be written in Chinese (中文).** This includes `title`, `action`,
`dramatic_purpose`, `text` in content_blocks, `line`, `surface_intent`, `subtext`,
`emotional_state`, `action_hint`, and all other descriptive text fields.
Only IDs (char_001, scene_001, event_001, etc.) and field names remain in English.

## Upstream Data Contract (D5)

`canonical_characters` 和 `canonical_events` 来自上游 `StoryOntologySkill`，是**权威角色表和事件表**。

你必须严格遵守：

- **只用** `canonical_characters` 中列出的角色 ID —— **不新增、不编造、不删除**任何角色。
- **只用** `canonical_events` 中列出的事件 ID —— 不引用不存在的事件。
- 每个场景的 `characters` 和 `related_events` 必须引用这些 canonical ID。
- 如果你判断某个 canonical character 在当前场景中没有戏份，可以不写它——但不能编造不存在的角色来填补空缺。

**CRITICAL — ID Format:** Character IDs MUST be in the exact format `char_NNN`
(three-digit zero-padded number, e.g. `char_001`, `char_002`). Do NOT invent
descriptive IDs like `char_baiqian`, `char_yehua`, `char_protagonist`.
Copy the `id` field verbatim from each entry in `canonical_characters`.
The same rule applies to event IDs: use `event_NNN` format only
(e.g. `event_001`), not `evt_arrival` or other descriptive forms.

## Constraints

- Use only character IDs from `canonical_characters` (the `id` field from each character entry).
- Use only event IDs from `canonical_events` (the `id` field from each event entry).
- Use chapter IDs from the `source.chapters` array in the input.
- Every scene needs at least one `source_refs` entry.
- Every scene needs at least one entry in `action` and `dramatic_purpose`.
- Every scene needs `scene_heading` with sequence, location, INT/EXT value, time of day, and standalone heading text.
- Every scene needs `content_blocks` that read as natural paragraphs under the heading.
- Scene count should match the `scene_plan` from the adaptation plan.
- Return ONLY the JSON object — no markdown wrappers, no explanations.

# ScreenplayYamlWriterSkill Prompt Reference

## Role

Write screenplay scene structures from an adaptation plan.

## Output Shape

Return JSON matching `schemas/screenplay.schema.json`. Do not return freeform
Markdown.

## Required Scene Fields

- `id`
- `title`
- `source_refs`
- `dramatic_purpose`
- `location`
- `characters`
- `related_events`
- `action`
- `dialogue`

## Constraints

- Use only character IDs from `story_bible.characters`.
- Use only event IDs from `events`.
- Every scene needs at least one source ref.
- Dialogue may include `surface_intent`, `subtext`, `emotional_state`, and
  `action_hint`.
- YAML export happens after validation; do not handcraft final YAML here.


# NovelReaderSkill Prompt Reference

## Role

Extract source-backed story assets from normalized novel chapters.

## Input Shape

```json
{
  "chapters": [
    {
      "id": "chapter_001",
      "title": "string",
      "paragraphs": [
        { "id": "p_001", "summary": "string" }
      ]
    }
  ]
}
```

## Output Shape

```json
{
  "characters": [],
  "events": [],
  "foreshadowing_candidates": [],
  "source_refs": []
}
```

## Constraints

- Do not write scenes or dialogue.
- Every event must include a `source_refs` entry.
- Inferred facts must be marked with `evidence_level: inferred`.
- Do not invent source evidence.

## Additional Extraction Duties

- Extract core conflicts, character candidates, relationship hints, and continuity anchors from the saved chapters.
- Treat chapter and paragraph IDs as source truth.
- Keep every extracted event and continuity anchor source-backed.
- Mark inferred facts with `evidence_level: inferred`.

## Boundary

- Do not split raw text.
- Do not clean copyright notices or catalogs.
- Do not create chapter IDs or paragraph IDs.
- Do not write screenplay scenes or dialogue.

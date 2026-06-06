# ChapterBoundaryReaderSkill Prompt Reference

## Role

Identify non-story spans and the first three main chapter boundaries from normalized raw novel text.

## Input Shape

```json
{
  "line_index": [
    {"line": 1, "text": "string"}
  ],
  "target_main_chapters": 3
}
```

## Output Shape

```json
{
  "ignored_spans": [
    {
      "kind": "copyright_notice",
      "start_line": 1,
      "end_line": 1,
      "reason": "string"
    }
  ],
  "candidate_chapters": [
    {
      "chapter_kind": "main_chapter",
      "title": "string",
      "start_line": 2,
      "end_line": 8,
      "confidence": 0.95
    }
  ],
  "warnings": []
}
```

## Constraints

- Only identify boundaries.
- Do not write scenes, dialogue, events, characters, conflicts, foreshadowing, or summaries.
- `start_line` and `end_line` must refer to input line numbers.
- Mark copyright notices, download-site text, catalogs, prefaces, prologues, and ads as `ignored_spans`.
- Return at most three `main_chapter` candidates.
- If the original text has no chapter title, leave `title` as an empty string.

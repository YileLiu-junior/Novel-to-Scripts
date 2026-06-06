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
- **ALL text fields MUST be written in Chinese (中文).** Character names, event titles, summaries,
  descriptions — all text content in Chinese. Only IDs (char_001, event_001, etc.) remain in English.

## Additional Extraction Duties

- Extract core conflicts, character candidates, relationship hints, and continuity anchors from the saved chapters.
- Treat chapter and paragraph IDs as source truth.
- Keep every extracted event and continuity anchor source-backed.
- Mark inferred facts with `evidence_level: inferred`.

## Chapter Reading Strategy

You will receive a list of chapters. Apply the following reading depth rules:

1. **Prologue Detection:** If the first chapter's title suggests it is a prologue, preface, or楔子
   (e.g. contains "序", "楔子", "前传", "引子", "前言") AND its body text exceeds **2000 characters**,
   treat it as `chapter_000` — the zero-th chapter. Short prefaces under 2000 characters are
   background context only and do NOT count as a numbered chapter.

2. **Deep-Read Chapters:** Deep-read the prologue chapter_000 (if it exists) and chapters 1, 2, 3.
   **Stop at the end of chapter 3.** Do not read or analyze chapters beyond chapter 3.
   For deep-read chapters, extract:
   - Every named character (with aliases, narrative role, relationships, source refs)
   - Every narrative event (with participants, summary, source refs)
   - Foreshadowing candidates and continuity anchors
   - Character knowledge states and dramatic conflicts

3. **Screenplay Boundary:** The final screenplay will only adapt events from deep-read chapters
   (prologue through chapter 3).

4. **Chapter Count:** If fewer than 4 chapters are provided, deep-read all available chapters.
   Do not invent chapters that were not provided.

## Boundary

- Do not split raw text.
- Do not clean copyright notices or catalogs.
- Do not create chapter IDs or paragraph IDs.
- Do not write screenplay scenes or dialogue.

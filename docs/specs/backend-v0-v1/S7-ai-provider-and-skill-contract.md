# S7 AI Provider And Skill Contract

## Owner

Skill Engineer.

## Purpose

Keep prompts and model calls inside the AI layer while making fake generation
stable enough for backend and frontend development.

## Files

- `backend/app/ai/providers/base.py`
- `backend/app/ai/providers/fake_provider.py`
- `backend/app/ai/providers/openai_provider.py`
- `backend/app/ai/skills/README.md`
- `backend/app/ai/skills/novel_reader.py`
- `backend/app/ai/skills/story_ontology.py`
- `backend/app/ai/skills/adaptation_planner.py`
- `backend/app/ai/skills/screenplay_writer.py`
- `backend/app/ai/skills/continuity_auditor.py`
- `backend/app/ai/skills/dialogue_doctor.py`
- `backend/app/ai/prompts/*.md`

## Required In V0+V1

- `FakeProvider`
- `NovelReaderSkill` minimal wrapper
- `StoryOntologySkill` minimal wrapper
- `AdaptationPlannerSkill`
- `ScreenplayYamlWriterSkill`

## Placeholders

- `OpenAIProvider`
- `ContinuityAuditorSkill`
- `DialogueDoctorSkill`

## Rules

- Skill wrappers accept structured input and return structured output.
- Skill wrappers do not save database records.
- Skill wrappers do not decide job state.
- Prompt text lives in `backend/app/ai/prompts/`.
- Business services must not import real model SDKs directly.

## Acceptance

- Fake provider returns deterministic output for the same inputs.
- Missing required fields in skill output can fail the orchestrator.
- Fake and real providers fit the same provider interface.


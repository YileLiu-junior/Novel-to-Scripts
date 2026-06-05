# S8 Orchestrator And Worker

## Owner

Backend Builder.

## Purpose

Connect V0+V1 generation stages into one recoverable backend pipeline.

## Files

- `backend/app/services/generation_orchestrator.py`
- `backend/app/services/job_service.py`
- `backend/app/services/artifact_service.py`
- `backend/app/services/llm_trace_service.py`
- `backend/app/workers/jobs.py`

## V0 Pipeline

```text
chapters
  -> ScreenplayYamlWriterSkill fake
  -> ValidationService
  -> YamlService
  -> screenplay_yaml artifact
```

## V1 Pipeline

```text
chapters
  -> NovelReaderSkill
  -> StoryOntologySkill
  -> AdaptationPlannerSkill
  -> ScreenplayYamlWriterSkill
  -> ValidationService
  -> YamlService
  -> minimal AuditReport
```

## Rules

- Use FastAPI `BackgroundTasks` for V1 async behavior.
- `workers/jobs.py` wraps background functions only.
- Do not introduce Redis.
- Every step failure writes `generation_jobs.error`.
- Every step success writes an artifact.

## Acceptance

- Fake provider can run the full V1 pipeline.
- Mid-pipeline failure marks job `failed`.
- Failure preserves `current_step` and error reason.
- Successful artifacts include `story_bible`, `adaptation_plan`,
  `screenplay_json`, and `screenplay_yaml`.


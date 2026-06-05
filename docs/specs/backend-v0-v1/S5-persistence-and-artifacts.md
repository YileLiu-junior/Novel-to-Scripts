# S5 Persistence And Artifacts

## Owner

Backend Builder.

## Purpose

Persist projects, chapters, jobs, artifacts, and LLM traces so the pipeline is
inspectable and retryable.

## Files

- `backend/app/db/session.py`
- `backend/app/db/tables.py`
- `backend/app/repositories/project_repository.py`
- `backend/app/repositories/chapter_repository.py`
- `backend/app/repositories/artifact_repository.py`
- `backend/app/repositories/job_repository.py`
- `backend/app/repositories/llm_run_repository.py`

## Minimal Tables

```text
projects
chapters
generation_jobs
artifacts
llm_runs
```

## Rules

- V1 uses SQLite.
- `artifacts.data` stores JSON objects or YAML strings.
- `artifacts.version` starts at 1 and increments per project and artifact type.
- Fake provider also writes an `llm_run` placeholder trace.
- Repositories expose persistence operations; services own orchestration.

## Acceptance

- Each successful generation step saves an artifact.
- Regenerating an artifact type increments version.
- Failed jobs keep already-created artifacts.


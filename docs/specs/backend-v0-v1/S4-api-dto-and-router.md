# S4 API DTO And Router Skeleton

## Owner

Backend Builder.

## Purpose

Define frontend/backend HTTP boundaries without putting business logic inside
routes.

## Files

- `backend/app/api/router.py`
- `backend/app/api/routes_projects.py`
- `backend/app/api/routes_chapters.py`
- `backend/app/api/routes_generation.py`
- `backend/app/api/routes_artifacts.py`
- `backend/app/api/routes_jobs.py`
- `backend/app/api/routes_yaml.py`
- `backend/app/api/routes_schema.py`
- `backend/app/api/routes_health.py`
- `backend/app/api/dto/*.py`
- `docs/api/api-contract.md`

## Minimal API

```text
POST   /api/projects
GET    /api/projects/{project_id}
PUT    /api/projects/{project_id}/chapters
GET    /api/projects/{project_id}/chapters
POST   /api/projects/{project_id}/generate/story-bible
POST   /api/projects/{project_id}/generate/adaptation-plan
POST   /api/projects/{project_id}/generate/screenplay
GET    /api/jobs/{job_id}
GET    /api/projects/{project_id}/artifacts
GET    /api/projects/{project_id}/artifacts/{type}
POST   /api/projects/{project_id}/yaml/validate
GET    /api/projects/{project_id}/yaml/download
GET    /api/projects/{project_id}/schema/download
```

## Rules

- Routes parse requests, call services, and return DTOs.
- Routes do not compose prompts.
- Routes do not call AI providers directly.
- Routes do not write SQL directly.

## Acceptance

- Two saved chapters cause generation requests to return a clear cannot-generate
  error.
- Three saved chapters can create a job.
- Job query returns `queued`, `running`, `succeeded`, or `failed`.


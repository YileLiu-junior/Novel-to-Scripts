# S3 Domain Models

## Owner

Backend Builder.

## Purpose

Turn fixtures and schema into backend internal truth with Pydantic models.

## Files

- `backend/app/domain/common.py`
- `backend/app/domain/project.py`
- `backend/app/domain/source.py`
- `backend/app/domain/story_bible.py`
- `backend/app/domain/adaptation.py`
- `backend/app/domain/screenplay.py`
- `backend/app/domain/audit.py`
- `backend/app/domain/artifacts.py`
- `backend/app/domain/jobs.py`
- `backend/app/domain/llm_runs.py`
- `backend/app/core/ids.py`

## Rules

- `domain/` imports Pydantic and standard library only.
- `domain/` must not import FastAPI, SQLAlchemy, OpenAI SDK, or repositories.
- Domain models express structure, not persistence behavior.
- Backend-generated IDs are represented as strings with documented prefixes.

## Tests

- `backend/tests/services/test_chapter_service.py`
- `backend/tests/validators/test_schema_validator.py`

## Acceptance

- Three chapters normalize into `chapter_001` through `chapter_003`.
- Paragraph IDs remain predictable when the same chapter text is saved again.
- Missing required fields fail Pydantic validation.


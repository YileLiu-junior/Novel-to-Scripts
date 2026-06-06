---
title: V0+V1 Backend Spec Work Design
created: 2026-06-05
status: approved-for-file-generation
source:
  - docs/plans/2026-06-05-004-project-directory-structure.md
  - docs/plans/2026-06-05-005-v1-backend-framework-and-agent-team-decision.md
  - docs/plans/2026-06-05-006-v0-v1-backend-spec-and-agent-team-plan.md
  - .tmp-novel-to-script-team/references/
---

# V0+V1 Backend Spec Work Design

## Goal

Generate S0-S10 backend specs and the matching contract artifacts for the AI
novel-to-screenplay workbench. The work should create enough structure for the
next agent or developer to implement safely without guessing field names,
directory boundaries, pipeline order, or skill responsibilities.

## Approved Approach

Create one spec document per step under `docs/specs/backend-v0-v1/`, plus the
reference assets each spec needs:

- `fixtures/` for shared JSON/YAML examples.
- `schemas/` for machine-readable screenplay schema and design notes.
- `backend/app/` skeletons for domain, API, AI, validators, services, workers,
  repositories, and exporters.
- `backend/app/ai/prompts/` and `backend/app/ai/skills/README.md` for skill
  contract and prompt format references.
- `docs/api/`, `docs/demo/`, and `docs/schema/` for review/demo handoff.

## Reference Adaptation

The temporary `novel-to-script-team` skill contributes:

- First principles: visualizable output, consistency, and gateable work.
- Review language: PASS/FAIL with location, problem, and action.
- Traceability: task state, logs, artifacts, and recoverable stages.

It does not contribute:

- Long episode production workflow.
- Storyboard, Seedance, image generation, or visual prompt workflows.
- Hit-script retrieval dependency.
- Runtime subagent orchestration.

## Architecture Boundary

The backend uses Python, FastAPI, Pydantic v2, SQLite, repository boundaries,
fake provider first, BackgroundTasks later, and deterministic validation before
YAML export.

The generated Python files are skeleton contracts, not a complete runnable
backend. Their purpose is to put call logic in the right locations and prevent
prompt, API, persistence, validation, and export responsibilities from mixing.

## Acceptance

This file generation pass is complete when:

- S0-S10 are present and internally aligned.
- Fixture and schema examples cover story bible, adaptation plan, screenplay,
  audit warnings, and invalid refs.
- Skill and prompt reference files describe expected structured inputs/outputs.
- Backend skeletons show the intended call flow.
- JSON and YAML examples parse successfully.


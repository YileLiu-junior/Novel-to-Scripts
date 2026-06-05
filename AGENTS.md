# Agent Operating Rules

This repository is the working space for an AI novel-to-screenplay workbench.
The current backend target is V0+V1: stable structured generation, artifact
tracking, validation, and YAML export before any real model quality push.

## Source Documents

- Product scope: `Pre-research/AI小说转剧本MVP方案细化.md`
- Directory architecture: `docs/plans/2026-06-05-004-project-directory-structure.md`
- Backend decision: `docs/plans/2026-06-05-005-v1-backend-framework-and-agent-team-decision.md`
- Spec sequence and team plan: `docs/plans/2026-06-05-006-v0-v1-backend-spec-and-agent-team-plan.md`
- Adapted reference ideas: `.tmp-novel-to-script-team/references/`

Use the temporary team references for quality gates, traceability, continuity,
and review language. Do not copy its long-episode production, storyboard,
image-generation, Seedance, or hit-script retrieval flows into this backend.

## Mission

Build a structured adaptation backend that can turn at least three novel
chapters into a traceable screenplay asset:

```text
chapters
  -> stable chapter and paragraph IDs
  -> fake structured AI artifacts
  -> minimal story bible
  -> adaptation config
  -> adaptation plan
  -> screenplay JSON
  -> deterministic validation
  -> YAML export
  -> minimal audit warnings
```

The product story is not "AI writes a beautiful script in one prompt." It is:
AI produces inspectable adaptation artifacts, while code enforces structure,
references, job state, and export reliability.

## V0+V1 Scope

V0 must support:

- Create a project.
- Save at least three chapters.
- Generate stable `chapter_###` and `p_###` IDs.
- Reject generation with fewer than three chapters.
- Run a fake pipeline to produce `screenplay_json`.
- Export `demo_screenplay.yaml`.
- View or download the schema.

V1 must support:

- `adaptation_config` with `target_format`, `fidelity_level`,
  `preserve_priorities`, and `dialogue_style`.
- `adaptation_plan` with retained, merged, deleted or deferred events,
  protected elements, and scene plan.
- Screenplay generation that consumes `adaptation_plan`.
- YAML containing both adaptation config and adaptation plan.
- One saved artifact per AI step.
- Queryable job state, current step, error, and artifact IDs.

## Non-Goals

Do not introduce these in V0+V1:

- Redis, Celery, RQ, or any external queue.
- PostgreSQL JSONB or graph databases.
- RDF or OWL ontology systems.
- Budget risk scoring.
- Final Draft or Fountain export.
- Multi-user collaboration.
- Complex version diff.
- Real subagent runtime in the product backend.
- Storyboard, video prompt, image generation, or hit-script retrieval flows.

Future versions may add richer story bible, causal graph, dialogue doctoring,
and audit loops by extending fields and services, not by replacing the V0+V1
pipeline.

## Directory Boundaries

- `fixtures/`: shared contract examples for backend, frontend, and tests.
- `schemas/`: machine-readable and human-readable screenplay schema assets.
- `backend/app/domain/`: Pydantic models only; no FastAPI, SQLAlchemy, or SDKs.
- `backend/app/api/`: HTTP DTOs and routers; no prompts or direct database code.
- `backend/app/services/`: workflow orchestration and use-case coordination.
- `backend/app/ai/providers/`: fake and real provider boundaries.
- `backend/app/ai/skills/`: skill wrappers; no database writes or job decisions.
- `backend/app/ai/prompts/`: prompt format references and prompt text.
- `backend/app/validators/`: deterministic validation; no model or network calls.
- `backend/app/exporters/`: pure export logic; no content repair.
- `backend/app/repositories/`: persistence access.
- `backend/app/workers/`: V1 background task boundary; no Redis dependency.
- `docs/specs/backend-v0-v1/`: S0-S10 implementation specs.

## Agent Team

- Showrunner: keeps V0+V1 scope, freezes demo path, owns gates.
- Contract Architect: owns fixtures, schema, ID rules, DTO/API contracts.
- Backend Builder: owns FastAPI, domain, services, repositories, workers, export.
- Skill Engineer: owns provider contracts, skill wrappers, prompt references.
- Validation Director: owns schema/reference validation and audit warning mapping.
- Review Director: gives PASS/FAIL at gates with location, problem, and action.
- Continuity Recorder: protects minimal events, foreshadowing, and knowledge state.
- Demo Producer: owns smoke path, demo checklist, and frozen example assets.

## Review Gates

Gate 0 Scope:

- Changes serve V0+V1 only.
- Future capabilities are reserved through fields or directories, not implemented.

Gate 1 Contract:

- Fixtures, schemas, Pydantic models, DTOs, and frontend expectations align.
- Field changes start in fixtures before code.

Gate 2 Backend Boundary:

- API does not compose prompts.
- Skills do not write database records.
- Validators do not call models.
- Exporters do not repair content.
- Services orchestrate; they do not hold large prompt bodies.

Gate 3 Artifact:

- Every pipeline step saves an artifact.
- Jobs expose status, current step, errors, and artifact IDs.
- Fake and real providers share the same orchestrator path.

Gate 4 Validation:

- Broken references are detected deterministically.
- Warnings point to concrete entity IDs.
- `fixtures/demo_invalid_refs.yaml` triggers expected findings.

Gate 5 Demo:

- Smoke path runs without a real API key.
- YAML is readable, parseable, and downloadable.
- Demo can explain structured adaptation, not black-box generation.

## Execution Order

Work in this order unless a later approved plan says otherwise:

```text
S0 agent rules
  -> S1 fixtures
  -> S2 schema and IDs
  -> S3 domain models
  -> S4 API DTO/router skeleton
  -> S5 persistence and artifacts
  -> S6 validators
  -> S7 fake provider and skills
  -> S8 orchestrator and worker
  -> S9 YAML/schema export
  -> S10 smoke and acceptance
```

The practical rule: fixture first, domain second, validators third, fake provider
fourth, orchestrator fifth, real provider last.


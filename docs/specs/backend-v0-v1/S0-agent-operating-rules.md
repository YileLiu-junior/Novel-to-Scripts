# S0 Agent Operating Rules

## Owner

Showrunner.

## Purpose

Make every agent follow the same product scope, directory boundaries, review
gates, and implementation order before backend work begins.

## Inputs

- `docs/plans/2026-06-05-004-project-directory-structure.md`
- `docs/plans/2026-06-05-005-v1-backend-framework-and-agent-team-decision.md`
- `docs/plans/2026-06-05-006-v0-v1-backend-spec-and-agent-team-plan.md`
- `Pre-research/AI小说转剧本MVP方案细化.md`
- `.tmp-novel-to-script-team/references/index.md`
- `.tmp-novel-to-script-team/references/00-first-principles.md`
- `.tmp-novel-to-script-team/references/04-review-gates.md`
- `.tmp-novel-to-script-team/references/21-agent-logging-standard.md`

## Output

- Root `AGENTS.md`
- This spec index under `docs/specs/backend-v0-v1/`

## Rules

- Treat 005 as the backend decision source.
- Treat 004 as the directory placement source.
- Use `.tmp-novel-to-script-team/references` only for gates, traceability,
  continuity, review language, and quality discipline.
- Do not copy storyboard, Seedance, image generation, or long-episode flows.
- Do not introduce runtime subagents in V0+V1.

## Acceptance

- An agent can read `AGENTS.md` and know where to put domain, API, prompts,
  validators, exporters, and workers.
- V0+V1 non-goals are explicit.
- Review gates use PASS/FAIL language with location, problem, and action.


---
plan_type: feat
created: 2026-06-07
status: active
---

# feat: Frontend-Backend Acceptance Implementation

**Origin:** `docs/superpowers/plans/2026-06-07-frontend-backend-acceptance-plan.md`

## Summary

Execute the frontend-backend acceptance plan: verify the acceptance script covers all V0+V1 endpoints, confirm frontend views correctly consume `api_client` wrappers per the handoff checklist, and run the engineering review gate (syntax check + live backend smoke test).

## Scope Boundaries

### In Scope
- Verify `scripts/frontend_backend_acceptance_check.py` covers all 8 acceptance steps
- Confirm `frontend/api_client.py` has all 16 required wrapper functions
- Confirm each frontend view page maps to its designated responsibility (Task 2 Step 2)
- Run syntax check and live acceptance test
- Fix any gaps found during verification

### Out of Scope
- Modifying `schemas/`
- Frontend directly reading `data/projects/...` runtime files
- Redis, Celery, real subagent runtime, Storyboard, video/image generation
- Model quality validation

---

## Implementation Units

### U1. Acceptance Script Completeness Audit

**Goal:** Verify the acceptance script covers all 8 steps from the origin plan and fix any gaps.

**Dependencies:** None

**Files:**
- `scripts/frontend_backend_acceptance_check.py` (read, potentially modify)

**Approach:** Compare the script's `AcceptanceRunner.run()` steps against the origin plan's Steps 1-8. The script already implements: health check, project creation, chapter intake (auto-split + GET), generation job polling, artifact verification (7 types), rendered preview/download, YAML validation, schema download, frontend-data init/get/put, and summary output. Confirm each assertion matches the plan's expected behavior.

**Test scenarios:**
- Syntax check: `python -m py_compile scripts/frontend_backend_acceptance_check.py` must exit 0
- Dry-run parse: `python scripts/frontend_backend_acceptance_check.py --help` must succeed
- The `rejects_two_chapters` step is a bonus addition beyond the plan — verify it doesn't interfere with the main flow

**Verification:** All 8 plan steps map to concrete `AcceptanceRunner` methods with matching assertions.

---

### U2. Frontend Handoff Checklist Verification

**Goal:** Confirm every required `api_client` wrapper exists and each frontend view page consumes the correct endpoints per Task 2 of the origin plan.

**Dependencies:** None (parallel with U1)

**Files:**
- `frontend/api_client.py` (read-only verification)
- `frontend/views/original.py` (read-only verification)
- `frontend/views/screenplay_preview.py` (read-only verification)
- `frontend/views/export.py` (read-only verification)
- `frontend/views/characters.py` (read-only verification)
- `frontend/views/scenes.py` (read-only verification)
- `frontend/views/plots.py` (read-only verification)
- `frontend/views/audit_report.py` (read-only verification)

**Approach:** Cross-reference the 16 required wrappers (Task 2 Step 1) against `api_client.py` exports. Then verify each view page's imports and API calls match its designated responsibility (Task 2 Step 2). Check that product boundary rules (Task 2 Step 3) are respected: frontend-data is treated as workspace state, not schema truth; fixtures are fallback-only.

**Test scenarios:**
- All 16 wrapper functions exist in `api_client.py` with matching signatures
- `original.py` calls: `create_project`, `auto_split_chapters`/`replace_chapters`, `list_chapters`, `generate_screenplay`, `get_job`, `list_artifacts`, `get_artifact`, `get_rendered`
- `screenplay_preview.py` calls: `get_rendered`, `download_rendered`
- `export.py` calls: `download_yaml`, `validate_yaml`, `download_schema`
- `characters.py` calls: `init_frontend_data`, `save_frontend_data`
- `scenes.py` calls: `init_frontend_data`, `save_frontend_data`
- `plots.py` calls: `init_frontend_data`, `save_frontend_data`
- `audit_report.py` calls: `get_artifact`
- No view directly reads `data/projects/` runtime files

**Verification:** All 16 wrappers confirmed present; all 7 views confirmed consuming correct endpoints; product boundaries respected.

---

### U3. Engineering Review Gate

**Goal:** Run the acceptance script against the live backend and produce the final acceptance summary.

**Dependencies:** U1, U2

**Files:**
- `scripts/frontend_backend_acceptance_check.py` (execute)
- `docs/superpowers/plans/2026-06-07-frontend-backend-acceptance-plan.md` (update with results)

**Approach:** Run syntax check first. If a live backend is available at `localhost:8000`, execute the full acceptance suite with `--timeout-seconds 180`. Capture PASS/FAIL output and the final ACCEPTANCE SUMMARY. If the backend is down, note this as a prerequisite gap.

**Test scenarios:**
- `python -m py_compile scripts/frontend_backend_acceptance_check.py` exits 0
- With live backend: all steps PASS, exit code 0
- Without live backend: health check FAIL is expected and reported

**Verification:** Syntax check passes. If live backend available, acceptance summary shows `failed: 0`.

---

## Key Technical Decisions

1. **No new code needed for frontend views** — all views already consume `api_client` correctly per the handoff checklist.
2. **Acceptance script is feature-complete** — the existing script covers all 8 plan steps plus a bonus `rejects_two_chapters` validation.
3. **Haiku model for sub-agents** — verification work is read-only analysis; Haiku is sufficient.

## Deferred to Follow-Up Work

- Real provider testing with DeepSeek API key (requires user's live environment)
- `fake` provider pathway hardening (noted as backend implementation gap in origin plan)

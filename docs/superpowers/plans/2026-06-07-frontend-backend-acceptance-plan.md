# Frontend Backend Acceptance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立一套可重复运行的前端接入后端验收方案，确认 live backend 已经能支撑前端从项目创建到生成、预览、导出和编辑态保存的主链路。

**Architecture:** 以后端 HTTP API 为唯一 runtime truth，前端本地缓存只保存映射和快照。验收脚本使用 Python stdlib 直接调用已经启动并跑通的 FastAPI live server，按前端实际接入顺序验证 endpoints、response shape、job state、artifact completeness、download content 和 `frontend-data` 编辑态。

**Tech Stack:** Python 3 stdlib (`argparse`, `json`, `urllib`, `time`), FastAPI backend at `http://localhost:8000`, Streamlit frontend contract wrappers in `frontend/api_client.py`.

---

## 验收边界

本计划只服务 V0+V1 前端接入确认：

- 覆盖创建项目、章节导入、生成 job、artifact 拉取、rendered 预览、YAML/Schema 下载、YAML 校验、`frontend-data` init/get/put。
- 不修改 `schemas/`。
- 不让前端直接读 `data/projects/...` runtime files。
- 不引入 Redis、Celery、真实 subagent runtime、Storyboard、video prompt 或 image generation。
- 不验证真实 model quality，只验证 stable structured generation 和 inspectable artifacts。
- 当前仓库实现中 `GenerationOrchestrator.from_provider_settings()` 要求 real provider；如果用 `XENGINEER_AI_PROVIDER=fake` 启动 live server，`POST /generate/screenplay` 会返回 500。验收脚本应连接“后端已经通路”的实际服务，例如用户已配置好的 DeepSeek backend。

## 文件结构

- Create: `scripts/frontend_backend_acceptance_check.py`
  - 责任：作为前端接入后端通路的 live smoke/acceptance checker。
  - 输入：`--base-url`、`--timeout-seconds`、`--poll-interval`、`--project-title`。
  - 输出：逐步骤 `PASS/FAIL`、失败 detail、最后 JSON summary。
- Modify: none for frontend/backend runtime code.
- Reference only: `frontend/api_client.py`, `backend/app/api/routes_*.py`, `backend/app/api/dto/*.py`.

## Task 1: Live Backend Acceptance Script

**Files:**
- Create: `scripts/frontend_backend_acceptance_check.py`

- [ ] **Step 1: Create stdlib HTTP helpers**

实现 `ApiError`、`request_json()`、`download()`、`assert_true()`，所有失败都带上 method/path/status/detail。

```python
class ApiError(RuntimeError):
    def __init__(self, method: str, path: str, status: int | None, detail: str) -> None:
        super().__init__(f"{method} {path} failed: {status or 'network'} {detail}")
        self.method = method
        self.path = path
        self.status = status
        self.detail = detail
```

- [ ] **Step 2: Verify backend health and project creation**

Run:

```powershell
python scripts/frontend_backend_acceptance_check.py --base-url http://localhost:8000
```

Expected if backend is down:

```text
FAIL health: GET /api/health failed
```

Expected if backend is up:

```text
PASS health
PASS create_project
```

- [ ] **Step 3: Verify chapter intake**

脚本先调用 `POST /api/projects/{project_id}/chapters/auto-split`，再调用 `GET /api/projects/{project_id}/chapters`。断言：

- `chapter_count >= 3`
- returned chapters length `>= 3`
- first chapter id starts with `chapter_`
- first paragraph id starts with `p_`

如果 auto-split 在某个环境不可用，脚本不 silently skip，直接 FAIL，因为当前前端接入方案依赖它。

- [ ] **Step 4: Verify full generation job**

调用：

```text
POST /api/projects/{project_id}/generate/screenplay
GET  /api/jobs/{job_id}
```

断言：

- generate response contains `job_id`
- job status eventually becomes `succeeded`
- failed job prints `error`
- succeeded job has non-empty `artifact_ids`

- [ ] **Step 5: Verify required artifacts**

调用：

```text
GET /api/projects/{project_id}/artifacts
GET /api/projects/{project_id}/artifacts/screenplay_json
GET /api/projects/{project_id}/artifacts/screenplay_yaml
GET /api/projects/{project_id}/artifacts/audit_report
GET /api/projects/{project_id}/artifacts/screenplay_rendered
```

断言：

- artifact list includes `screenplay_json`, `screenplay_yaml`, `audit_report`, `screenplay_rendered`
- `screenplay_json.data.scenes` is a non-empty list
- `screenplay_json.data.adaptation_config` exists
- `screenplay_json.data.adaptation_plan` exists
- `screenplay_yaml.data` is non-empty string

- [ ] **Step 6: Verify preview, download, validation, schema**

调用：

```text
GET  /api/projects/{project_id}/screenplay/rendered?format=markdown
GET  /api/projects/{project_id}/screenplay/rendered?format=text
GET  /api/projects/{project_id}/screenplay/rendered/download?format=markdown
GET  /api/projects/{project_id}/screenplay/rendered/download?format=text
GET  /api/projects/{project_id}/yaml/download
POST /api/projects/{project_id}/yaml/validate
GET  /api/projects/{project_id}/schema/download
```

断言：

- markdown/text preview `content` is non-empty
- downloads return non-empty bytes
- yaml validation returns `findings` list
- schema response contains `schema_text`

- [ ] **Step 7: Verify frontend editable data**

调用：

```text
POST /api/projects/{project_id}/frontend-data/init
GET  /api/projects/{project_id}/frontend-data
PUT  /api/projects/{project_id}/frontend-data
```

断言：

- init returns lists for `characters`, `character_relations`, `scenes`, `scene_relations`, `plots`, `causal_relations`
- get returns same top-level keys
- put preserves all top-level lists and increments/updates `meta`

- [ ] **Step 8: Produce acceptance summary**

脚本最后输出：

```text
ACCEPTANCE SUMMARY
passed: N
failed: 0
project_id: project_xxx
job_id: job_xxx
```

失败时 exit code must be `1`; 全部通过时 exit code must be `0`。

## Task 2: Frontend Handoff Checklist

**Files:**
- Modify: `docs/superpowers/plans/2026-06-07-frontend-backend-acceptance-plan.md`

- [ ] **Step 1: Confirm frontend code maps to the same endpoints**

检查 `frontend/api_client.py` 是否已有 wrapper：

- `create_project`
- `auto_split_chapters`
- `replace_chapters`
- `list_chapters`
- `generate_screenplay`
- `get_job`
- `list_artifacts`
- `get_artifact`
- `get_rendered`
- `download_yaml`
- `download_rendered`
- `download_schema`
- `validate_yaml`
- `init_frontend_data`
- `get_frontend_data`
- `save_frontend_data`

- [ ] **Step 2: Confirm page responsibilities**

验收确认：

- `original.py` handles chapter import, generate, job polling, artifact refresh.
- `screenplay_preview.py` consumes rendered preview/download only.
- `export.py` consumes YAML download/validation/schema only.
- `characters.py`, `scenes.py`, `plots.py` consume and save `frontend-data`.
- `audit_report.py` consumes `audit_report` artifact.

- [ ] **Step 3: Confirm product boundary**

在前端文案和行为里保持：

- `frontend-data` 是前端工作台编辑态，不等同于 schema truth。
- 如果 backend 没有提供回写 screenplay/YAML 的接口，不承诺编辑后 YAML 同步更新。
- fixtures 只做 fallback，不做主 runtime。

## Task 3: Engineering Review Gate

**Files:**
- Modify: `docs/superpowers/plans/2026-06-07-frontend-backend-acceptance-plan.md`

- [ ] **Step 1: Run acceptance script syntax check**

```powershell
python -m py_compile scripts/frontend_backend_acceptance_check.py
```

Expected: exit code `0`.

- [ ] **Step 2: Run live backend check when server is available**

```powershell
python scripts/frontend_backend_acceptance_check.py --base-url http://localhost:8000 --timeout-seconds 180
```

Expected: exit code `0`, all steps PASS. 如果第一步 health 失败，说明 server 未启动；如果 generation 返回 500，先检查 live backend 是否按当前实现配置了 `XENGINEER_AI_PROVIDER=deepseek` 和有效 API key。

- [ ] **Step 3: Run plan-eng-review**

Use `plan-eng-review` against this plan and the script output. The review must answer:

- Does the script cover the real frontend minimum integration flow?
- Are failure modes specific enough for frontend developers?
- Are any V0+V1 boundaries violated?
- Is the plan clear enough for another agent or frontend engineer to execute?

## Self-Review

Spec coverage:

- Project/chapter/generate/job/artifact/render/export/schema/frontend-data are covered.
- Frontend handoff boundaries are covered.
- V0+V1 non-goals remain out of scope.

Placeholder scan:

- No TBD/TODO/fill-in placeholders remain.

Type consistency:

- Endpoint names match `frontend/api_client.py` wrappers and `backend/app/api/routes_*.py` routes.

## Acceptance Owner Notes

验收时请记录：

- backend provider mode: 当前 live acceptance 以 `deepseek` 通路为准；`fake` 通路若失败，应作为后端实现缺口单独记录，不阻塞前端对已通路 backend 的接入验收。
- command used
- project_id
- job_id
- failed step if any
- whether `frontend-data` save is expected to affect YAML in this backend version

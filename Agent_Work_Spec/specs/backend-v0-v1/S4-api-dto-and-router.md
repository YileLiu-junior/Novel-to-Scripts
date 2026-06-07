# S4 API DTO 与 Router 骨架

## 负责人

后端构建者（Backend Builder）。

## 目的

定义 frontend/backend 的 HTTP 边界，让 routes 只负责请求解析、服务调用和 DTO 返回，不把 business logic 放进 route 层。

## 文件

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

## 最小 API

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

## 规则

- Routes 解析 requests，调用 services，并返回 DTOs。
- Routes 不 compose prompts。
- Routes 不直接调用 AI providers。
- Routes 不直接写 SQL。

## 验收标准

- 保存两章时，generation requests 返回清晰的 `cannot-generate` error。
- 保存三章后，可以创建一个 job。
- Job query 返回 `queued`、`running`、`succeeded` 或 `failed`。

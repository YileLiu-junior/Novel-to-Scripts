# V0+V1 API 契约

本文档定义了前端和冒烟测试所依赖的后端 API 形态。路由文件目前均为骨架实现，尚未完成。

## Projects

```text
POST /api/projects
GET  /api/projects/{project_id}
```

创建和查看项目。

## Chapters

```text
PUT  /api/projects/{project_id}/chapters
GET  /api/projects/{project_id}/chapters
```

保存和读取源素材章节。由后端负责分配稳定的 chapter 和 paragraph ID。

进入生成阶段前必须拒绝不足三章的 project。

## Generation

```text
POST /api/projects/{project_id}/generate/story-bible
POST /api/projects/{project_id}/generate/adaptation-plan
POST /api/projects/{project_id}/generate/screenplay
```

触发生成任务，创建 job 并返回 job ID。V1 使用 FastAPI BackgroundTasks，不引入 Redis 或 Celery。

## Jobs

```text
GET /api/jobs/{job_id}
```

Job 响应体包含：

- `id`
- `project_id`
- `status`：`queued`、`running`、`succeeded` 或 `failed`
- `current_step`
- `error`
- `artifact_ids`

## Artifacts

```text
GET /api/projects/{project_id}/artifacts
GET /api/projects/{project_id}/artifacts/{type}
```

Artifact 类型：

- `novel_analysis`
- `story_bible`
- `adaptation_plan`
- `screenplay_json`
- `screenplay_yaml`
- `audit_report`

## YAML

```text
POST /api/projects/{project_id}/yaml/validate
GET  /api/projects/{project_id}/yaml/download
```

校验接口将 YAML 解析为 JSON 后执行 schema 校验和引用校验，返回警告/错误。

下载接口需要已存在 `screenplay_json` 或 `screenplay_yaml` 类型的 artifact。

## Schema

```text
GET /api/projects/{project_id}/schema/download
```

返回 `schemas/screenplay.schema.json` 或等效的 schema 内容。
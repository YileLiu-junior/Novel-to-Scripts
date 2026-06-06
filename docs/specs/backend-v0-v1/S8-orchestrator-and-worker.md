# S8 Orchestrator 与 Worker

## 负责人

后端构建者（Backend Builder）。

## 目的

把 V0+V1 generation stages 串成一条可恢复的 backend pipeline。

## 文件

- `backend/app/services/generation_orchestrator.py`
- `backend/app/services/job_service.py`
- `backend/app/services/artifact_service.py`
- `backend/app/services/llm_trace_service.py`
- `backend/app/workers/jobs.py`

## V0 Pipeline

```text
chapters
  -> ScreenplayYamlWriterSkill fake
  -> ValidationService
  -> YamlService
  -> screenplay_yaml artifact
```

## V1 Pipeline

```text
chapters
  -> NovelReaderSkill
  -> StoryOntologySkill
  -> AdaptationPlannerSkill
  -> ScreenplayYamlWriterSkill
  -> ValidationService
  -> YamlService
  -> minimal AuditReport
```

## 规则

- 使用 FastAPI `BackgroundTasks` 提供 V1 async behavior。
- `workers/jobs.py` 只封装 background functions。
- 不引入 Redis。
- 每个 step failure 都写入 `generation_jobs.error`。
- 每个 step success 都保存一个 artifact。

## 验收标准

- Fake provider 能跑完整 V1 pipeline。
- Pipeline 中途失败时，job 标记为 `failed`。
- Failure 保留 `current_step` 和 error reason。
- 成功 artifacts 包含 `story_bible`、`adaptation_plan`、`screenplay_json` 和 `screenplay_yaml`。

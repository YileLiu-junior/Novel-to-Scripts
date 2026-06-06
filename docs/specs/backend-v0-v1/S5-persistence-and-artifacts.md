# S5 持久化与产物

## 负责人

后端构建者（Backend Builder）。

## 目的

用本地文件存储持久化项目、章节、任务、产物和 LLM 追踪记录，使流水线可审查、可重试，并避免 V0+V1 引入数据库迁移、连接管理或外部服务复杂度。

## 文件

- `backend/app/repositories/base.py`
- `backend/app/repositories/local/store.py`
- `backend/app/repositories/local/project_repository.py`
- `backend/app/repositories/local/chapter_repository.py`
- `backend/app/repositories/local/job_repository.py`
- `backend/app/repositories/local/artifact_repository.py`
- `backend/app/repositories/local/llm_run_repository.py`

## 本地存储目录契约

默认存储根目录为 `data/`，可通过后端配置覆盖。所有文件都使用 UTF-8 编码，JSON 文件使用 stable key order，便于 demo diff、人工检查和测试断言。该目录是 backend-owned local storage，前端和脚本只能通过 API 或 backend service 读取，不直接改写。

```text
data/
  projects.json
  projects/
    {project_id}/
      chapters.json
      jobs.json
      artifacts/
        novel_analysis_v001.json
        story_bible_v001.json
        adaptation_plan_v001.json
        screenplay_json_v001.json
        screenplay_yaml_v001.yaml
        audit_report_v001.json
  llm_runs.jsonl
```

最小实体文件：

```text
projects.json
projects/{project_id}/chapters.json
projects/{project_id}/jobs.json
projects/{project_id}/artifacts/{artifact_type}_v###.json
projects/{project_id}/artifacts/screenplay_yaml_v###.yaml
llm_runs.jsonl
```

## 规则

- V1 使用本地文件存储，不使用 SQLite、PostgreSQL、Redis 或外部对象存储。
- Repository 层只暴露按领域对象读写的持久化操作；Service 层负责编排，不直接拼接本地路径。
- `ProjectRepository` 负责创建、读取和更新 `data/projects.json` 中的 project index。
- `ChapterRepository` 负责读写 `projects/{project_id}/chapters.json`，并保持 `chapter_###` 和 `p_###` ID 稳定。
- `JobRepository` 负责读写 `projects/{project_id}/jobs.json`，保存 job status、current step、error 和 artifact IDs。
- `ArtifactRepository` 负责保存每一步 artifact，`version` 从 1 开始，按 `project_id + artifact_type` 递增。
- `ArtifactRepository` 使用 `{artifact_type}_v###.json` 或 `{artifact_type}_v###.yaml` 文件名表达版本，读取最新产物时按同一 artifact type 的最大版本号解析。
- `LlmRunRepository` 负责向 `data/llm_runs.jsonl` 追加每次 provider 调用 trace；每条 trace 必须包含 `project_id` 和 `job_id`，Fake provider 同样写入 `llm_run` 占位追踪记录。
- artifact 数据优先保存为 JSON object；`screenplay_yaml` 这类导出结果可以在 artifact `data` 中保存 YAML 字符串。
- 写文件必须采用临时文件 + atomic replace，避免生成中断留下半个 JSON 文件。
- `llm_runs.jsonl` 每行是一条完整 JSON record，追加失败不能破坏已有行；读取时遇到损坏行必须返回可定位错误。
- 本地存储只在单进程 V0+V1 demo 中保证一致性；并发、多用户和跨机器存储属于后续版本。

## 验收标准

- 每个成功的生成步骤保存一个产物。
- 重新生成同一产物类型时版本号递增。
- 失败的任务保留已创建的产物。
- 关闭后端后重新启动，仍能通过 local repositories 读取项目、章节、job、artifact 和 llm run。
- 删除或破坏单个 artifact 文件时，错误能定位到具体 `project_id`、`artifact_type` 和版本文件名。

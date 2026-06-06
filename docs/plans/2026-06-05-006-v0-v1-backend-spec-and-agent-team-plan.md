---
title: AI 小说转剧本 V0+V1 后端 Spec 与 Agent Team 工作流计划
status: active
origin:
  - Pre-research/AI小说转剧本MVP方案细化.md
  - docs/plans/2026-06-05-004-project-directory-structure.md
  - docs/plans/2026-06-05-005-v1-backend-framework-and-agent-team-decision.md
  - .tmp-novel-to-script-team/AGENTS.md
  - .tmp-novel-to-script-team/AGENT-STATE-GUIDE.md
created: 2026-06-05
---

# AI 小说转剧本 V0+V1 后端 Spec 与 Agent Team 工作流计划

## 1. 目标

本计划回答两个问题：

1. 要做到 V0+V1，后端 spec 应该按什么顺序写。
2. 开发时 Agent Team 应该如何分工、审核和交接。

V0+V1 的后端目标不是先追求模型写得漂亮，而是先把这条链路稳定跑通：

```text
3 章以上小说输入
  -> 稳定章节/段落 ID
  -> FakeProvider 生成结构化 artifact
  -> 最小故事圣经
  -> 可控改编配置
  -> 改编计划
  -> 故事梗概/大纲/文学剧本结构
  -> 动作/情节/情境/主题/主人公/人物关系索引
  -> 剧本 JSON
  -> 引用校验
  -> YAML 导出
  -> 最小 audit warning
```

其中“最小故事圣经”虽然来自后续 V2 的产品概念，但在 V0+V1 后端里应作为技术底座保留；否则 `adaptation_plan` 没有稳定的人物、事件、伏笔引用，V1 的“可控改编”会变成 prompt 口号。

## 2. Scope

### 2.1 V0 必须完成

- 支持创建项目。
- 支持保存至少 3 个章节。
- 后端生成稳定 `chapter_###`、`p_###`。
- 能用 fake pipeline 生成基础 `screenplay_json`。
- `screenplay_json` 必须以 `scene` 为基本单位，且每场包含 `scene_heading` 和 `content_blocks`。
- 能导出 `demo_screenplay.yaml`。
- 能下载或查看 Schema。
- 少于 3 章时后端拒绝生成。

### 2.2 V1 必须完成

- 支持 `adaptation_config`：
  - `target_format`
  - `fidelity_level`
  - `preserve_priorities`
  - `dialogue_style`
- 支持生成 `adaptation_plan`：
  - `retained_events`
  - `merged_events`
  - `deleted_or_deferred_events`
  - `protected_elements`
  - `scene_plan`
- 剧本生成必须消费 `adaptation_plan`，不能绕过。
- YAML 中必须写入 `adaptation_config` 和 `adaptation_plan`。
- YAML 中必须写入 `script_structure` 和 `core_elements`，用于承接文学剧本格式和核心元素要求。
- 每个 AI step 都保存 artifact。
- 每个 job 可查询状态、当前阶段、错误和产物 ID。

### 2.3 V0+V1 预留但不展开

- `story_bible.characters`
- `relationship_edges`
- `knowledge_states`
- `events`
- `causal_graph.edges`
- `foreshadowing`
- `DialogueLine.subtext`
- `audit_report`

V0+V1 必须正式支持，不作为未来预留：

- `script_structure.story_synopsis`
- `script_structure.story_outline`
- `script_structure.literary_screenplay`
- `core_elements.actions`
- `core_elements.plot`
- `core_elements.situations`
- `core_elements.theme`
- `core_elements.protagonists`
- `core_elements.character_relationships`
- `scenes[].scene_heading`
- `scenes[].content_blocks`

这些字段可以有最小实现，目的是给 V2/V3/V4/V5 留窗口，不在本阶段做复杂编辑器、图谱、批注协作或长剧生产流。

### 2.4 本阶段明确不做

- Redis / Celery / RQ。
- PostgreSQL JSONB。
- 图数据库。
- RDF/OWL。
- 预算风险。
- Final Draft / Fountain。
- 多人协作。
- 复杂版本 diff。
- 真实 subagent runtime。

## 3. Spec 写作顺序

不要一开始写“大而全后端 spec”。推荐按下面 10 个 spec 小步推进，每一步都要有可检查产物。

| 顺序 | Spec | 目的 | 主要产物 | 主责 Agent |
| --- | --- | --- | --- | --- |
| S0 | Agent 操作规则 | 让所有开发 agent 遵守同一套边界 | `AGENTS.md` | Showrunner |
| S1 | Fixture 契约 | 锁前后端共同语言 | `fixtures/*.json`、`fixtures/*.yaml` | Contract Architect |
| S2 | Schema 与 ID 规则 | 锁结构可信底座 | `schemas/screenplay.schema.json`、ID 规则 | Contract Architect |
| S3 | Domain 模型 | 把契约落成 Pydantic | `backend/app/domain/` | Backend Builder |
| S4 | API DTO 与路由 | 让前端能对接 mock/真实 API | `backend/app/api/` | Backend Builder |
| S5 | Persistence 与 artifact | 保存 job、artifact、llm trace | `backend/app/repositories/local/` | Backend Builder |
| S6 | Validator | 保证引用和结构可信 | `backend/app/validators/` | Validation Director |
| S7 | FakeProvider 与 Skill contract | 不依赖真实模型跑通 pipeline | `backend/app/ai/` | Skill Engineer |
| S8 | Orchestrator 与 worker | 串联 V0+V1 生成链路 | `generation_orchestrator.py`、`workers/jobs.py` | Backend Builder |
| S9 | YAML/Schema 导出 | 满足交付和评审展示 | `exporters/`、`services/yaml_service.py` | Backend Builder |
| S10 | Smoke 与验收 | 证明端到端可跑 | `scripts/run_demo_smoke.py`、测试 | Review Director |

正确节奏是：

```text
先写 fixture
  -> 再写 domain
  -> 再写 validator
  -> 再写 fake provider
  -> 再串 orchestrator
  -> 最后接真实 provider
```

不要先写 prompt。prompt 只能填结构，不能定义结构。

## 4. Backend Implementation Units

### U1: 项目操作规则与 AGENTS.md

目标：把 005 决策变成所有 agent 的执行规则。

文件：

- `AGENTS.md`
- `docs/plans/2026-06-05-005-v1-backend-framework-and-agent-team-decision.md`
- `docs/plans/2026-06-05-004-project-directory-structure.md`

内容要求：

- 写清项目使命：结构化小说改编工作台。
- 写清 V0+V1 范围。
- 写清 non-goals。
- 写清目录边界。
- 写清 Agent Team 分工。
- 写清 review gates。
- 链接 004、005 和 MVP 方案，不复制全文。

验收：

- 任意 agent 读完 `AGENTS.md` 后能知道哪里写 domain、哪里写 API、哪里写 prompt。
- `AGENTS.md` 不应变成完整 PRD，也不应复制目录树全文。

### U2: Fixture 与 Schema 契约

目标：先锁定前后端共同契约。

文件：

- `fixtures/demo_novel_3_chapters.json`
- `fixtures/demo_story_bible.json`
- `fixtures/demo_screenplay.json`
- `fixtures/demo_screenplay.yaml`
- `fixtures/demo_audit_report.json`
- `fixtures/demo_invalid_refs.yaml`
- `schemas/screenplay.schema.json`
- `schemas/screenplay.schema.yaml`
- `schemas/screenplay-schema-design.md`

决策：

- 内部真相源是 JSON/Pydantic。
- YAML 是导出结果和用户可编辑格式。
- fixture 必须先于 domain/API 改动。

测试场景：

- `demo_novel_3_chapters.json` 至少包含 3 章。
- 至少 2 个角色、3 个事件、1 条关系、1 个伏笔、2 场 scene。
- 每场 scene 至少有 `scene_heading`、`content_blocks`、`action` 和 `dialogue`。
- 顶层必须有 `script_structure` 和 `core_elements`。
- `demo_invalid_refs.yaml` 至少包含一个不存在的 `character_id` 或 `event_id`。

### U3: Domain 模型与 ID 服务

目标：把契约落成后端内部真相源。

文件：

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

决策：

- `domain/` 只 import Pydantic 和标准库。
- `domain/` 不 import FastAPI、SQLAlchemy、OpenAI SDK。
- 章节、段落、场景、台词、warning ID 由后端生成。
- scene heading、content block、outline、core action、situation ID 也必须稳定可预测，不能让模型随意漂移。

测试文件：

- `backend/tests/services/test_chapter_service.py`
- `backend/tests/validators/test_schema_validator.py`

测试场景：

- 3 章输入生成稳定 `chapter_001` 到 `chapter_003`。
- 段落 ID 在重复保存同一章节时保持可预测。
- 缺少必填字段时 Pydantic 校验失败。

### U4: API DTO 与 Router Skeleton

目标：先建立前后端对接边界，不把业务逻辑写进路由。

文件：

- `backend/app/api/router.py`
- `backend/app/api/routes_projects.py`
- `backend/app/api/routes_chapters.py`
- `backend/app/api/routes_generation.py`
- `backend/app/api/routes_artifacts.py`
- `backend/app/api/routes_jobs.py`
- `backend/app/api/routes_yaml.py`
- `backend/app/api/routes_schema.py`
- `backend/app/api/routes_health.py`
- `backend/app/api/dto/projects.py`
- `backend/app/api/dto/chapters.py`
- `backend/app/api/dto/generation.py`
- `backend/app/api/dto/artifacts.py`
- `backend/app/api/dto/jobs.py`
- `backend/app/api/dto/yaml.py`
- `backend/app/api/dto/schema.py`

最小 API：

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

测试文件：

- `backend/tests/api/test_chapters_api.py`
- `backend/tests/api/test_generation_api.py`
- `backend/tests/api/test_yaml_api.py`

测试场景：

- 保存 2 章后，生成接口返回不可生成或错误。
- 保存 3 章后，生成接口能创建 job。
- job 查询返回 `queued/running/succeeded/failed`。

### U5: Local File Storage、Repository 与 Artifact

目标：让每一步生成都可保存、可追踪、可重试。

文件：

- `backend/app/repositories/base.py`
- `backend/app/repositories/local/store.py`
- `backend/app/repositories/local/project_repository.py`
- `backend/app/repositories/local/chapter_repository.py`
- `backend/app/repositories/local/job_repository.py`
- `backend/app/repositories/local/artifact_repository.py`
- `backend/app/repositories/local/llm_run_repository.py`

最小文件契约：

```text
data/projects.json
data/projects/{project_id}/chapters.json
data/projects/{project_id}/jobs.json
data/projects/{project_id}/artifacts/{artifact_type}_v###.json
data/projects/{project_id}/artifacts/screenplay_yaml_v###.yaml
data/llm_runs.jsonl
```

决策：

- V1 使用 backend-owned local file storage，不引入 SQLite。
- `artifacts.data` 可以保存 JSON object 或 YAML string。
- artifact 文件名使用 `{artifact_type}_v###.json` 或 `{artifact_type}_v###.yaml`，版本从 1 开始递增。
- `llm_runs.jsonl` 即使 fake provider 也要能写占位 trace，方便未来接真实模型。

测试文件：

- `backend/tests/services/test_generation_orchestrator.py`

测试场景：

- 每个生成阶段完成后保存 artifact。
- 同类型 artifact 再生成时版本递增。
- job 失败时保留已生成 artifact。

### U6: Validator

目标：把结构可信交给确定性代码。

文件：

- `backend/app/validators/chapter_validator.py`
- `backend/app/validators/schema_validator.py`
- `backend/app/validators/reference_validator.py`
- `backend/app/validators/audit_validator.py`
- `backend/app/services/validation_service.py`

最小规则：

- `source_refs.chapter_id` 必须存在。
- `scene.characters[]` 必须存在于 `story_bible.characters`。
- `dialogue.character_id` 必须属于当前 scene characters。
- `related_events[]` 必须存在于 `events`。
- `causal_graph.edges.from/to` 必须存在于 `events`。
- `foreshadowing.setup_event_id` 必须存在。
- `foreshadowing.payoff_scene_id` 如果非空，必须存在于 `scenes`。
- `script_structure.story_outline.related_events[]` 必须存在于 `events`。
- `script_structure.literary_screenplay.scene_ids[]` 必须存在于 `scenes`。
- `core_elements.protagonists[]` 必须存在于 `story_bible.characters`。
- `core_elements.actions[].scene_id` 和 `core_elements.situations[].scene_id` 必须存在于 `scenes`。
- `content_blocks.character_id` 必须属于当前 scene characters。

测试文件：

- `backend/tests/validators/test_reference_validator.py`
- `backend/tests/validators/test_schema_validator.py`

测试场景：

- 引用不存在角色时返回 error。
- 引用不存在事件时返回 warning 或 error。
- `demo_invalid_refs.yaml` 能触发预期 warning。
- validator 不调用模型、不依赖网络。

### U7: AI Provider 与 Skill Wrapper

目标：把 prompt 和模型调用隔离在 AI 层。

文件：

- `backend/app/ai/providers/base.py`
- `backend/app/ai/providers/fake_provider.py`
- `backend/app/ai/providers/openai_provider.py`
- `backend/app/ai/skills/novel_reader.py`
- `backend/app/ai/skills/story_ontology.py`
- `backend/app/ai/skills/adaptation_planner.py`
- `backend/app/ai/skills/screenplay_writer.py`
- `backend/app/ai/skills/continuity_auditor.py`
- `backend/app/ai/skills/dialogue_doctor.py`
- `backend/app/ai/prompts/*.md`

V0+V1 必须实现：

- `FakeProvider`
- `NovelReaderSkill` 最小 wrapper
- `StoryOntologySkill` 最小 wrapper
- `AdaptationPlannerSkill`
- `ScreenplayYamlWriterSkill`

可占位：

- `OpenAIProvider`
- `ContinuityAuditorSkill`
- `DialogueDoctorSkill`

测试文件：

- `backend/tests/ai/test_fake_provider.py`
- `backend/tests/ai/test_skill_contracts.py`

测试场景：

- fake provider 对同一输入返回稳定结构。
- skill wrapper 返回缺字段时，orchestrator 能标记 job failed。
- 业务 service 不直接 import 真实模型 SDK。

### U8: Generation Orchestrator 与 Worker

目标：串联 V0+V1 后端主链路。

文件：

- `backend/app/services/generation_orchestrator.py`
- `backend/app/services/job_service.py`
- `backend/app/services/artifact_service.py`
- `backend/app/services/llm_trace_service.py`
- `backend/app/workers/jobs.py`

V0 pipeline：

```text
chapters
  -> ScreenplayYamlWriterSkill fake
  -> ValidationService
  -> YamlService
  -> screenplay_yaml artifact
```

V1 pipeline：

```text
chapters
  -> NovelReaderSkill
  -> StoryOntologySkill
  -> AdaptationPlannerSkill
  -> ScreenplayYamlWriterSkill
  -> script_structure/core_elements normalization
  -> ValidationService
  -> YamlService
  -> minimal AuditReport
```

决策：

- V1 使用 FastAPI `BackgroundTasks`。
- `workers/jobs.py` 只包装后台任务，不引入 Redis。
- 每一步失败都写入 `jobs.json` 中对应 job 的 `error`。
- 每一步成功都写入 artifact。

测试文件：

- `backend/tests/services/test_generation_orchestrator.py`

测试场景：

- FakeProvider 跑完整 V1 pipeline。
- 中间阶段失败时 job 变为 `failed`。
- 失败时保留 `current_step` 和错误原因。
- 成功后 artifact 列表包含 `story_bible`、`adaptation_plan`、`screenplay_json`、`screenplay_yaml`。

### U9: YAML 与 Schema 导出

目标：满足比赛和 demo 的可见交付。

文件：

- `backend/app/exporters/yaml_exporter.py`
- `backend/app/exporters/schema_exporter.py`
- `backend/app/services/yaml_service.py`
- `backend/app/services/schema_service.py`
- `schemas/screenplay.schema.json`
- `schemas/screenplay.schema.yaml`
- `docs/schema/screenplay-schema-explained.md`

决策：

- 导出只序列化已验证结构。
- `exporters/` 不补字段、不修复模型输出。
- 用户编辑 YAML 后，必须解析回 JSON 再校验。

测试文件：

- `backend/tests/services/test_yaml_service.py`
- `backend/tests/api/test_yaml_api.py`

测试场景：

- YAML 导出后可 parse 回 JSON。
- YAML validate 能返回 warning 列表。
- 没有 `screenplay_json` 时 download 返回明确错误。

### U10: Smoke Script 与 Demo Freeze

目标：证明后端已经能被前端和 demo 使用。

文件：

- `scripts/run_demo_smoke.py`
- `scripts/validate_fixtures.py`
- `docs/demo/demo-checklist.md`
- `docs/api/api-contract.md`

Smoke path：

```text
读取 fixtures/demo_novel_3_chapters.json
  -> 创建项目
  -> 保存章节
  -> fake 生成 story_bible
  -> fake 生成 adaptation_plan
  -> fake 生成 screenplay_json
  -> 引用校验
  -> 导出 demo_screenplay.yaml
  -> 用 demo_invalid_refs.yaml 验证 warning
```

验收：

- smoke path 可以在无真实 API key 的情况下跑通。
- 输出 YAML 可读、可解析、可下载。
- 至少展示一条定位到 scene/dialogue/event 的 warning。

## 5. Agent Team 工作流设置

### 5.1 总原则

复用 `.tmp-novel-to-script-team` 的工作流思想：

```text
生成 -> 校验 -> 审核 -> 回改 -> 复审
```

但本项目不要照搬它的 Markdown-only 产物。V0+V1 应把旧工作流产品化为：

```text
jobs.json
artifacts
llm_runs.jsonl
audit_report
validation warnings
```

也就是说：开发阶段可以用 Agent Team 分工；产品运行时先不实现真实 subagent runtime。

### 5.2 推荐角色

| Agent | 开发职责 | 不负责 |
| --- | --- | --- |
| Showrunner | 守住 V0+V1 范围、排优先级、冻结 demo path | 写具体 prompt 或路由细节 |
| Contract Architect | fixture、schema、ID、DTO、API 契约 | 模型质量调优 |
| Backend Builder | FastAPI、domain、service、repository、worker、exporter | 创作判断 |
| Skill Engineer | provider、skill wrapper、prompt、fake response | 保存持久化文件、决定 job 状态 |
| Validation Director | schema/reference validator、audit warning 映射 | 重写创作内容 |
| Review Director | 按 gate 做 PASS/FAIL、阻止坏结构进入下一阶段 | 直接扩大 scope |
| Continuity Recorder | 维护事件、伏笔、知识状态的最小连续性视图 | 做复杂图谱 |
| Frontend Workbench Builder | 基于 fixture/API 展示工作台 | 在前端实现复杂引用校验 |
| Demo Producer | 准备样例、彩排 smoke、冻结演示叙事 | Day 3 加新功能 |

### 5.3 每个 spec 的执行模板

每个 Agent 接 spec 时都按同一格式交付：

```text
Input
  - 读哪些上游文档
  - 读哪些 fixture/schema

Work
  - 改哪些文件
  - 哪些边界不能碰

Output
  - 生成什么 artifact/doc/code
  - 测试或检查怎么证明可用

Review
  - Validation Director 检查结构
  - Review Director 给 PASS/FAIL
```

### 5.4 Review Gates

#### Gate 0: Scope Gate

主责：Showrunner。

通过条件：

- 改动只服务 V0+V1。
- 没有引入预算风险、图数据库、多人协作、Final Draft 等非目标。
- 未来窗口通过字段或目录预留，不实现复杂功能。

#### Gate 1: Contract Gate

主责：Contract Architect + Validation Director。

通过条件：

- fixture 已更新。
- Schema 已同步。
- Pydantic 模型与 fixture 对齐。
- 前端 mock client 不需要猜字段。

#### Gate 2: Backend Boundary Gate

主责：Backend Builder + Review Director。

通过条件：

- API 不拼 prompt。
- `ai/skills/` 不写持久化文件。
- `validators/` 不调用模型。
- `exporters/` 不修复内容。
- `services/` 只编排流程，不塞巨大 prompt。

#### Gate 3: Artifact Gate

主责：Backend Builder。

通过条件：

- 每个 pipeline step 有 artifact。
- job 能查状态和错误。
- fake provider 和真实 provider 共用 orchestrator。

#### Gate 4: Validation Gate

主责：Validation Director。

通过条件：

- 断裂引用能被发现。
- warning 能定位到实体 ID。
- `demo_invalid_refs.yaml` 能触发预期结果。

#### Gate 5: Demo Gate

主责：Demo Producer + Review Director。

通过条件：

- 无 API key 可跑 smoke。
- 可讲清“不是黑箱生成，而是结构化改编工作台”。
- Day 3 只修阻塞和打磨，不再扩功能。

### 5.5 Agent 调度顺序

推荐按这条线推进：

```text
1. Showrunner 写/确认 AGENTS.md
2. Contract Architect 锁 fixture + schema + ID
3. Validation Director 写 validator 测试清单
4. Backend Builder 搭 FastAPI/domain/repository skeleton
5. Skill Engineer 做 FakeProvider + skill contract
6. Backend Builder 串 generation_orchestrator
7. Validation Director 接入 reference/schema validation
8. Backend Builder 接 YAML export
9. Review Director 跑 gate review
10. Demo Producer 跑 smoke path
11. Skill Engineer 再接真实 provider
```

每一步都应该能留下一个明确产物，不要出现“我调了几个 prompt 但没有 artifact”的状态。

## 6. 开发排期建议

### Day 0: 开工前 60-90 分钟

目标：锁 spec，不写业务代码。

- 新建/更新 `AGENTS.md`。
- 锁 3-6 份 fixture。
- 锁 schema 顶层结构。
- 锁 ID 规则。
- 锁 smoke path。

完成标准：

- 后端、前端、prompt 都知道同一套字段。

### Day 1: Contract + V0 后端

目标：V0 能跑。

- 创建 FastAPI 后端骨架。
- 创建 Pydantic domain。
- 创建 chapter/project API。
- 创建 FakeProvider。
- 创建 YAML exporter。
- 跑通 3 章 -> 基础 screenplay_yaml。

完成标准：

- 2 章失败，3 章通过。
- fake 生成基础 YAML。
- YAML 可 parse。

### Day 2: V1 可控改编

目标：V1 有工作台感。

- 实现 `adaptation_config` DTO/model。
- 实现 `AdaptationPlannerSkill` fake output。
- 实现 `adaptation_plan` artifact。
- screenplay 生成消费 `adaptation_plan`。
- YAML 中包含改编配置和改编计划。

完成标准：

- 高忠实度配置进入 pipeline。
- `protected_elements` 不被 screenplay 阶段丢掉。
- job/artifact 可查看。

### Day 3: 审查与 demo

目标：把“结构可信”讲清楚。

- 接入最小 `audit_report`。
- `demo_invalid_refs.yaml` 触发 warning。
- 写 schema 说明。
- 跑 smoke script。
- 冻结 demo path。

完成标准：

- 真实模型即使暂时不稳，fake path 也能完整演示。
- 至少一条 warning 能定位到具体 scene/dialogue/event。

## 7. 测试矩阵

| 层级 | 测试文件 | 必测场景 |
| --- | --- | --- |
| chapter | `backend/tests/services/test_chapter_service.py` | 2 章失败、3 章通过、段落 ID 稳定 |
| API | `backend/tests/api/test_chapters_api.py` | 保存章节返回补全 ID 和 validation |
| API | `backend/tests/api/test_generation_api.py` | 创建 job、查询 job、失败返回 current_step |
| AI | `backend/tests/ai/test_fake_provider.py` | fake 输出稳定 |
| AI | `backend/tests/ai/test_skill_contracts.py` | skill 输出缺字段时失败 |
| validator | `backend/tests/validators/test_reference_validator.py` | 断裂 character/event/scene 引用 |
| YAML | `backend/tests/services/test_yaml_service.py` | JSON -> YAML -> JSON 回读 |
| smoke | `scripts/run_demo_smoke.py` | 端到端 fake pipeline |

## 8. 后续版本窗口

V0+V1 完成时要确保后续不用推翻架构：

- V2 故事圣经增强：扩 `story_bible`，不改 API 主线。
- V3 因果链：扩 `events`、`causal_graph`、`foreshadowing`，不引入图数据库。
- V4 潜台词：扩 `DialogueLine` 和 `DialogueDoctorSkill`，不改 scene 基本结构。
- V5 审查闭环：扩 `audit_report` 和 warning 状态，不重写 validation service。
- 生产化：local file storage 换 PostgreSQL 或对象存储，BackgroundTasks 换 RQ/Celery，但保留 repository 和 worker 边界。

## 9. 立刻下一步

推荐下一步先做两件事：

1. 生成根目录 `AGENTS.md`，把 005 决策压缩成项目操作规则。
2. 写 `fixtures/demo_novel_3_chapters.json`、`fixtures/demo_story_bible.json`、`fixtures/demo_screenplay.yaml`，让 Contract Architect 先把字段锁住。

这两件事完成后，再正式进入后端代码实现。否则后端很容易先搭出 API，却没有稳定契约可测。

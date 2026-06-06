---
title: AI 小说转剧本 V1 后端框架与 Agent Team 工作流决策
status: active
origin:
  - Pre-research/AI小说转剧本MVP方案细化.md
  - docs/plans/2026-06-05-001-architecture-ai-novel-to-script-plan.md
  - docs/plans/2026-06-05-003-phase-1-contract-model-api-schema.md
  - docs/plans/2026-06-05-004-project-directory-structure.md
  - .tmp-novel-to-script-team/AGENTS.md
  - .tmp-novel-to-script-team/AGENT-STATE-GUIDE.md
created: 2026-06-05
---

# AI 小说转剧本 V1 后端框架与 Agent Team 工作流决策

## 1. 决策摘要

V1 后端推荐采用：

```text
Python + FastAPI + Pydantic v2 + local file storage + artifact/job pipeline
```

配套策略：

- 前端用 `React + TypeScript + Vite` 做创作者工作台。
- 后端用 `FastAPI + Pydantic` 做结构可信中心。
- 内部真相源使用 JSON/Pydantic，不直接把 YAML 字符串当业务数据。
- 模型输出优先要求 JSON，后端校验后再导出 YAML。
- AI skill 负责创作判断，代码负责结构可信。
- V1 先用 `FakeProvider` 跑通 pipeline，再接真实 LLM provider。
- V1 用 FastAPI `BackgroundTasks` 和 local job state，不引入 Redis/Celery。
- V1 不做图数据库、预算风险、多人协作、Final Draft/Fountain 导出。

一句话：

> V1 不是先做一个会胡写的 AI 编剧，而是先做一个结构可信、可追溯、可校验、可继续扩展的小说改编工作台后端。

## 2. 背景与问题

当前项目定位是：

> 面向小说作者的 AI 改编工作台：用轻量故事本体和 YAML Schema，把 3 个章节以上的小说转成可审查、可编辑、可继续打磨的结构化剧本初稿。

它要解决的问题不是“AI 能不能写出剧本”，而是：

- 作者不知道 AI 为什么删改情节。
- 原著伏笔容易在摘要或改编时丢失。
- 角色目标、秘密、知识状态无法稳定追踪。
- 台词容易把潜台词直接说穿。
- 最终产物如果只是文本，就不可校验、不可追溯、不可长期编辑。

因此 V1 后端最重要的能力不是“模型调用”，而是：

```text
章节结构
  -> 原著解析 artifact
  -> 故事圣经 artifact
  -> 改编计划 artifact
  -> 剧本 JSON artifact
  -> 引用校验
  -> YAML 导出
  -> 审查 warning
```

## 3. gstack 决策结论

本决策来自三层 review 口径。

### 3.1 Office Hours 结论

真正痛点不是一键生成剧本，而是作者不信任黑箱改编。

V1 应该把产品叙事压成：

- 作者先控制改编尺度。
- AI 先读懂原著资产。
- 每场戏保留来源、目的、角色、事件、伏笔。
- 生成结果不是一次性文本，而是可继续编辑的剧本工程文件。

所以 V1 不应该追求“全自动编剧”，而应该追求：

```text
可控改编 + 结构化输出 + 可追溯来源 + 可校验引用
```

### 3.2 CEO Review 结论

不要扩大成完整编剧平台。

V1 最锋利的范围是：

- 多章节输入。
- 故事圣经。
- 可控改编策略。
- 剧本 JSON/YAML。
- Schema 和引用校验。
- 最小审查 warning。

暂缓：

- 预算风险。
- 制片可拍性评分。
- 复杂图谱。
- 多人协作。
- 长剧工业级版本 diff。
- Final Draft / Fountain。

V1 的目标应该是让评审和用户立刻看懂：

> 这个产品不是普通 prompt 包装，而是把 AI 改编过程结构化、可追溯、可审查。

### 3.3 Eng Review 结论

后端核心不是 prompt，而是契约、校验、artifact、可恢复 pipeline。

工程上必须坚持：

- 数据契约先行，prompt 后置。
- 内部 JSON/Pydantic，外部 YAML。
- 每个 AI step 都保存 artifact。
- 每个 artifact 都可以被前端展示和后续 step 复用。
- 每个生成 job 都可以查询状态、失败原因和已生成 artifact。
- 每个引用关系必须由代码校验。

如果这些不成立，后续 V2/V3/V4 的故事圣经、因果链、潜台词、审查闭环都会返工。

## 4. V1 推荐后端框架

### 4.1 API 框架

使用 `FastAPI`。

职责：

- 提供项目、章节、生成任务、artifact、YAML、Schema API。
- 输出 OpenAPI，供前端类型生成和接口对齐。
- 统一错误响应，保证 AI 失败时前端能展示“失败在哪一步”。

推荐路由：

```text
POST   /api/projects
GET    /api/projects/{project_id}

PUT    /api/projects/{project_id}/chapters
POST   /api/projects/{project_id}/chapters/auto-split
GET    /api/projects/{project_id}/chapters

POST   /api/projects/{project_id}/generate/story-bible
POST   /api/projects/{project_id}/generate/adaptation-plan
POST   /api/projects/{project_id}/generate/screenplay
POST   /api/projects/{project_id}/generate/audit

GET    /api/jobs/{job_id}

GET    /api/projects/{project_id}/artifacts
GET    /api/projects/{project_id}/artifacts/{type}

POST   /api/projects/{project_id}/yaml/validate
GET    /api/projects/{project_id}/yaml/download
GET    /api/projects/{project_id}/schema/download
```

### 4.2 领域模型层

使用 `Pydantic v2`。

核心模型：

- `Project`
- `Chapter`
- `Paragraph`
- `SourceRef`
- `StoryBible`
- `Character`
- `RelationshipEdge`
- `KnowledgeState`
- `Event`
- `CausalEdge`
- `Foreshadowing`
- `AdaptationConfig`
- `AdaptationPlan`
- `ScenePlan`
- `Scene`
- `DialogueLine`
- `AuditReport`
- `AuditWarning`
- `Artifact`
- `GenerationJob`
- `LlmRun`

规则：

- `domain/` 只定义类型和枚举，不 import FastAPI、SQLAlchemy、OpenAI SDK。
- 章节、段落、场景、warning ID 由后端生成。
- 角色、事件、伏笔可以由模型建议，但后端负责去重和稳定化。
- 所有跨实体引用都必须能被 `ValidationService` 检查。

### 4.3 存储层

V1 使用 backend-owned local file storage。

最小文件契约：

```text
data/projects.json
data/projects/{project_id}/chapters.json
data/projects/{project_id}/jobs.json
data/projects/{project_id}/artifacts/{artifact_type}_v###.json
data/projects/{project_id}/artifacts/screenplay_yaml_v###.yaml
data/llm_runs.jsonl
```

`artifacts` 保存每个阶段的结构化结果：

- `novel_analysis`
- `story_bible`
- `adaptation_plan`
- `screenplay_json`
- `screenplay_yaml`
- `audit_report`

`llm_runs.jsonl` 保存每次模型调用的追踪记录：

- prompt version
- provider
- model name
- request id
- token usage
- latency
- raw output
- parsed output
- validation errors

这样可以定位 AI 输出不稳定到底发生在哪一步。Service 只依赖 repository contract，不直接读写这些文件。

### 4.4 AI Provider 层

定义统一接口：

```text
generate_structured(prompt, schema, temperature, max_tokens)
generate_text(prompt, temperature, max_tokens)
```

V1 至少实现：

- `FakeProvider`
- `OpenAIProvider` 或其他真实 provider 的接口占位

`FakeProvider` 必须优先完成，因为它让前端、后端、校验、导出不被真实模型拖住。

业务层不直接依赖任何模型 SDK。

### 4.5 Skill Wrapper 层

V1 推荐实现以下 wrapper：

- `NovelReaderSkill`
- `StoryOntologySkill`
- `AdaptationPlannerSkill`
- `ScreenplayYamlWriterSkill`
- `ContinuityAuditorSkill` 最小版
- `DialogueDoctorSkill` 可只做 1-2 场关键戏

每个 wrapper 只负责：

```text
结构化输入 -> prompt -> provider -> 解析结构化输出
```

它不负责：

- 保存持久化文件。
- 决定 job 状态。
- 生成最终 YAML。
- 悄悄补全断裂 ID。
- 跳过后端校验。

### 4.6 Orchestrator 层

核心文件：

```text
backend/app/services/generation_orchestrator.py
```

职责：

```text
load artifacts
  -> call skill
  -> validate output
  -> save artifact
  -> update job
```

V1 的 pipeline：

```text
1. NovelReaderSkill
2. StoryOntologySkill
3. AdaptationPlannerSkill
4. ScreenplayYamlWriterSkill
5. ValidationService
6. YamlService
7. ContinuityAuditorSkill
```

要求：

- 每一步可单独重试。
- 每一步失败都写入 job error。
- 每一步输出都落 artifact。
- fake provider 和真实 provider 使用同一条 orchestrator。

### 4.7 校验与导出层

校验分两层：

1. 结构校验：
   - 字段是否存在。
   - 类型是否正确。
   - 枚举是否合法。

2. 引用校验：
   - `source_refs.chapter_id` 是否存在。
   - `scene.characters[]` 是否存在于 `story_bible.characters`。
   - `dialogue.character_id` 是否属于当前 scene characters。
   - `related_events[]` 是否存在于 `events`。
   - `causal_graph.edges.from/to` 是否存在于 `events`。
   - `foreshadowing.setup_event_id` 是否存在。
   - `foreshadowing.payoff_scene_id` 如果非空，是否存在于 `scenes`。

导出策略：

```text
Pydantic model
  -> JSON object
  -> reference validation
  -> YAML export
```

不要把模型输出的 YAML 原样当最终结果。

## 5. V1 不做什么

V1 明确不做：

- Redis / Celery / RQ 队列。
- PostgreSQL JSONB。
- 图数据库。
- RDF/OWL 本体。
- 多人协作。
- 版本 diff。
- 预算风险模块。
- 制片可拍性评分。
- Final Draft / Fountain 导出。
- 复杂拖拽图谱。
- 生产级权限、计费、团队空间。

V1 可以预留目录和接口，但不实现这些能力。

## 6. 给后续版本留窗口

### 6.1 V2：故事圣经增强

现在预留：

- `story_bible.characters`
- `relationship_edges`
- `knowledge_states`
- `voice_profile`
- `source_refs`
- `evidence_level`

未来可加：

- 人物卡编辑。
- 关系演进。
- 角色知识状态时间线。
- 原文证据视图。

### 6.2 V3：因果链与伏笔守护

现在预留：

- `events`
- `causal_graph.edges`
- `foreshadowing`
- `scene.related_events`
- `scene.foreshadowing`

未来可加：

- 未兑现伏笔面板。
- 因果边解释。
- 角色知道不该知道的信息 warning。
- scene 与 event 的双向定位。

### 6.3 V4：角色声音与潜台词

现在预留：

- `Character.voice_profile`
- `DialogueLine.surface_intent`
- `DialogueLine.subtext`
- `DialogueLine.emotional_state`
- `DialogueLine.action_hint`

未来可加：

- 单句重写。
- 角色声口对比。
- 解释型对白 warning。
- 潜台词强度评估。

### 6.4 V5：审查闭环

现在预留：

- `audit_report`
- `AuditWarning`
- `warning.target`
- `needs_human_review`

未来可加：

- 一键结构修复。
- warning 定位 scene/dialogue/event。
- 人工确认状态。
- 审查前后版本对比。

### 6.5 生产化

现在预留：

- `workers/jobs.py`
- `jobs.json`
- `artifacts.version`
- `llm_runs.jsonl`
- `repositories/`

未来可替换：

- local file storage -> PostgreSQL JSONB 或对象存储。
- BackgroundTasks -> RQ/Celery + Redis。
- 单模型 provider -> 多模型 fallback。
- 本地 demo -> 私有化部署。

## 7. Agent Team 工作流方案

### 7.1 复用原则

`.tmp-novel-to-script-team` 里可复用的是流程思想，不是直接照搬 Markdown 产物。

可复用：

- Showrunner 编排。
- 多 Agent 分工。
- 生成 -> 审核 -> 回改 -> 复审。
- Resumable Subagents 的状态思想。
- 审核门控。
- 连续性记录。
- 日志记录规范。

不直接照搬：

- Markdown-only 输出。
- 分集长剧生产流程。
- 分镜视频化流程。
- 复杂素材生成流程。
- 爆款剧本检索依赖。

本项目要把它产品化成：

```text
job state
artifact version
llm run trace
validation warning
structured JSON/YAML contract
```

### 7.2 Agent Team 角色

#### Showrunner

职责：

- 守住产品主线。
- 决定 V1 范围和砍功能顺序。
- 协调各 agent 的产物进入同一条 pipeline。
- 确保 demo 路径可讲、可跑、可验证。

#### Contract Architect

职责：

- 维护实体模型、ID 规则、API 契约、YAML Schema。
- 先改 fixture，再改模型和接口。
- 防止 prompt 先行导致字段漂移。

#### Backend Builder

职责：

- 实现 FastAPI、service、repository、job、artifact、YAML export。
- 保证 fake provider 能跑完整 smoke path。
- 不把业务逻辑散落到 API 路由里。

#### Skill Engineer

职责：

- 编写 prompt。
- 封装 skill wrapper。
- 维护 fake provider 和真实 provider。
- 记录 prompt version 和 LLM run trace。

#### Validation Director

职责：

- 写引用校验。
- 写 Schema 校验。
- 把校验问题转成 `AuditWarning`。
- 维护 `demo_invalid_refs.yaml`。

#### Review Director

职责：

- 对阶段产物做 PASS/FAIL。
- 失败必须给出位置、问题、修改动作。
- 阻止坏结构进入下一阶段。

#### Continuity Recorder

职责：

- 记录关键剧情资产。
- 记录伏笔、角色知识状态、关键决策。
- 把连续性风险写入 audit report 或 project memory。

#### Frontend Workbench Builder

职责：

- 用 fixture 先跑通 UI。
- 做章节输入、故事圣经、改编策略、剧本 YAML、审查面板。
- 不在前端实现复杂引用校验。

#### Demo Producer

职责：

- 维护示例小说、示例 YAML、演示脚本。
- 冻结 demo 路径。
- 在 Day 3 只修阻塞问题，不加新功能。

### 7.3 Agent 调度流程

V1 推荐流程：

```text
1. Contract Architect 锁 fixture 和 schema
2. Backend Builder 搭 FastAPI + Pydantic + FakeProvider
3. Skill Engineer 实现 NovelReaderSkill wrapper
4. Review Director 审核 novel_analysis artifact
5. Skill Engineer 实现 StoryOntologySkill wrapper
6. Validation Director 校验 story_bible 引用和 evidence_level
7. Skill Engineer 实现 AdaptationPlannerSkill wrapper
8. Review Director 审核 adaptation_plan 是否保留受保护元素
9. Skill Engineer 实现 ScreenplayYamlWriterSkill wrapper
10. Validation Director 校验 scenes/dialogue/source_refs
11. Backend Builder 导出 YAML
12. Continuity Recorder 生成最小 audit_report
13. Frontend Workbench Builder 接入 artifact 展示
14. Demo Producer 跑 smoke path 和 demo 彩排
```

每个阶段都走：

```text
生成 -> 校验 -> 审核 -> 保存 artifact -> 进入下一阶段
```

### 7.4 Agent State 映射

旧 team 的 `.agent-state.json` 思想可以映射到 V1 后端：

| 旧机制 | V1 后端映射 | 用途 |
| --- | --- | --- |
| `outputs/{剧本名}/.agent-state.json` | `jobs.json` | 保存当前生成任务状态 |
| agentId resume | `artifact.version` + `source_job_id` | 从上一步产物恢复 |
| agent 日志 | `llm_runs.jsonl` + backend logs | 追踪模型调用和解析错误 |
| 阶段产物 Markdown | `artifacts.data` | 保存结构化结果 |
| review log | `audit_report` + job error | 保存失败原因和 warning |

V1 不一定需要真实 subagent runtime，但必须保留：

- job 可查询。
- artifact 可复用。
- 每一步可重试。
- 每次模型调用可追踪。

## 8. 推荐目录对齐

本文档对应的目录方案以：

```text
docs/plans/2026-06-05-004-project-directory-structure.md
```

为准。

关键目录：

```text
backend/app/domain/
backend/app/api/
backend/app/repositories/
backend/app/repositories/local/
backend/app/services/
backend/app/validators/
backend/app/ai/providers/
backend/app/ai/skills/
backend/app/ai/prompts/
backend/app/workers/
backend/app/exporters/
backend/tests/

frontend/src/api/
frontend/src/features/
frontend/src/components/

fixtures/
schemas/
docs/api/
docs/demo/
scripts/
```

目录边界：

- `domain/` 定义类型。
- `api/` 处理 HTTP。
- `services/` 编排业务流程。
- `ai/skills/` 封装模型调用。
- `validators/` 做确定性校验。
- `exporters/` 做纯导出。
- `repositories/` 做持久化。
- `fixtures/` 做前后端共同契约。

## 9. 测试与验收

### 9.1 后端测试

第一阶段至少覆盖：

- 输入 2 章时校验失败。
- 输入 3 章时校验通过。
- 章节正文能稳定分段并生成 paragraph refs。
- `FakeProvider` 能跑完整 generation job。
- skill wrapper 输出缺字段时，job 状态变为 `failed`。
- 引用不存在的 `character_id` 会产生 error。
- 引用不存在的 `event_id` 会产生 warning 或 error。
- YAML 导出后可以 parse 回同等结构。
- `demo_invalid_refs.yaml` 能触发预期 warning。

### 9.2 前端测试

第一阶段至少覆盖：

- 少于 3 章时生成按钮 disabled。
- 生成 job 轮询中显示当前阶段。
- 故事圣经面板能读取 fixture。
- 场景详情能显示 source refs、related events、foreshadowing。
- YAML 下载按钮在无 screenplay 时 disabled。
- warning 点击后能定位到目标 scene 或 dialogue。

### 9.3 Smoke Path

第一条端到端 smoke path：

```text
读取 fixtures/demo_novel_3_chapters.json
  -> 创建项目和章节
  -> FakeProvider 生成 story_bible artifact
  -> FakeProvider 生成 adaptation_plan artifact
  -> FakeProvider 生成 screenplay_json artifact
  -> ValidationService 做引用校验
  -> YamlService 导出 demo_screenplay.yaml
  -> 用 demo_invalid_refs.yaml 验证 warning 展示
```

这条路径跑通后，真实模型接入才值得开始。

## 10. AGENTS.md 应该如何引用本决策

`AGENTS.md` 不应该原样复制 MVP 方案，也不应该原样复制目录结构全文。

它应该压缩成可执行规则：

- 项目使命。
- V1 范围。
- Non-goals。
- 架构边界。
- 目录职责。
- Agent team 工作流。
- Review gates。
- Source docs 链接。

建议 `AGENTS.md` 把本文作为上游决策引用：

```text
docs/plans/2026-06-05-005-v1-backend-framework-and-agent-team-decision.md
```

需要实现时读目录文档：

```text
docs/plans/2026-06-05-004-project-directory-structure.md
```

需要理解产品范围时读 MVP 方案：

```text
Pre-research/AI小说转剧本MVP方案细化.md
```

## 11. 下一步行动

推荐下一步按这个顺序做：

1. 新建 `AGENTS.md`，写入项目使命、V1 范围、架构规则和 Agent workflow 摘要。
2. 锁定三份核心 fixture：
   - `fixtures/demo_novel_3_chapters.json`
   - `fixtures/demo_story_bible.json`
   - `fixtures/demo_screenplay.yaml`
3. 新建 `backend/app/domain/`，先落 Pydantic 模型。
4. 新建 `backend/app/api/`，先落 router skeleton。
5. 新建 `backend/app/ai/providers/fake_provider.py`，跑通 fake generation。
6. 新建 `backend/app/validators/reference_validator.py`，先做引用校验。
7. 新建 `backend/app/exporters/yaml_exporter.py`，实现 JSON -> YAML。
8. 写 `scripts/run_demo_smoke.py`，验证 fake pipeline。

完成标准：

```text
创建项目
  -> 保存 3 章
  -> fake 生成故事圣经
  -> fake 生成改编计划
  -> fake 生成剧本 JSON
  -> 校验引用
  -> 导出 YAML
  -> 展示一条 warning
```

## 12. 最终判断

V1 后端的成败不取决于模型一次写得多漂亮，而取决于这几件事是否稳定：

- 章节和段落 ID 稳定。
- 人物、事件、场景、台词引用可校验。
- 每一步 AI 产物可保存、可查看、可重试。
- 内部 JSON/Pydantic 与外部 YAML 分离。
- fake provider 能独立跑通全链路。
- 真实 LLM 输出不稳定时，系统能指出失败阶段和原因。

因此，V1 的工程策略应该是：

> 先把结构可信和工作流可恢复做出来，再追求生成质量。

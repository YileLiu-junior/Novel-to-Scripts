# Agent Operating Rules（Agent 操作规则）

本仓库是一个“AI 小说转剧本”工作台的工程空间。
当前 backend target 是 V0+V1：先做好 stable structured generation、artifact tracking、validation 和 YAML export，再推进真实 model quality。

## Source Documents（源文档）

- 产品范围：`Pre-research/AI小说转剧本MVP方案细化.md`
- Directory architecture：`docs/plans/2026-06-05-004-project-directory-structure.md`
- Backend decision：`docs/plans/2026-06-05-005-v1-backend-framework-and-agent-team-decision.md`
- Spec sequence and team plan：`docs/plans/2026-06-05-006-v0-v1-backend-spec-and-agent-team-plan.md`
- Adapted reference ideas：`.tmp-novel-to-script-team/references/`

临时团队参考资料只用于 quality gates、traceability、continuity 和 review language。不要把其中的 long-episode production、storyboard、image generation、Seedance 或 hit-script retrieval flows 复制进当前 backend。

## Mission（使命）

构建一个 structured adaptation backend，能把至少三章小说转换成 traceable screenplay asset：

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

Product story 不是“AI 一次 prompt 写出漂亮剧本”。真正的 product story 是：AI 产出 inspectable adaptation artifacts，代码负责 enforce structure、references、job state 和 export reliability。

## V0+V1 Scope（范围）

V0 必须支持：

- Create a project。
- Save 至少三章 chapters。
- Generate stable `chapter_###` 和 `p_###` IDs。
- Reject generation when fewer than three chapters。
- Run a fake pipeline to produce `screenplay_json`。
- Export `demo_screenplay.yaml`。
- View or download the schema。

V1 必须支持：

- `adaptation_config`，包含 `target_format`、`fidelity_level`、`preserve_priorities` 和 `dialogue_style`。
- `adaptation_plan`，包含 retained、merged、deleted or deferred events，protected elements，以及 scene plan。
- Screenplay generation 必须 consume `adaptation_plan`。
- YAML 必须同时包含 adaptation config 和 adaptation plan。
- 每一个 AI step 都要保存一个 artifact。
- Job state 可查询，包括 status、current step、error 和 artifact IDs。

## Non-Goals（非目标）

V0+V1 不要引入：

- Redis、Celery、RQ 或任何外部队列。
- PostgreSQL JSONB 或图数据库。
- RDF 或 OWL 本体系统。
- 预算风险评分。
- Final Draft 或 Fountain 导出。
- 多用户协作。
- 复杂版本 diff。
- 产品 backend 里的真实 subagent runtime。
- Storyboard、video prompt、image generation 或 hit-script retrieval flows。

Future versions 可以通过扩展 fields 和 services 加入更丰富的 story bible、causal graph、dialogue doctoring 和 audit loops，但不要替换 V0+V1 pipeline。

## Directory Boundaries（目录边界）

- `fixtures/`：backend、frontend 和 tests 共享的 contract examples。
- `schemas/`：machine-readable 和 human-readable screenplay schema assets。
- `backend/app/domain/`：只放 Pydantic models；不能依赖 FastAPI、SQLAlchemy 或 SDK。
- `backend/app/api/`：HTTP DTOs 和 routers；不能放 prompts，也不能直接写 database code。
- `backend/app/services/`：workflow orchestration 和 use-case coordination。
- `backend/app/ai/providers/`：fake provider 和 real provider 的边界。
- `backend/app/ai/skills/`：skill wrappers；不能写数据库，也不能决定 job 流程。
- `backend/app/ai/prompts/`：prompt 格式参考和 prompt 文本。
- `backend/app/validators/`：deterministic validation；不能调用 models 或 network。
- `backend/app/exporters/`：pure export logic；不能 repair content。
- `backend/app/repositories/`：persistence access。
- `backend/app/workers/`：V1 background task boundary；不能依赖 Redis。
- `docs/specs/backend-v0-v1/`：S0-S10 implementation specs。

## Frontend-Backend Contract（前后端契约与并行开发规则）

以下规则是 V0+V1 前后端分离开发的基础，确保双方能独立工作、互不阻塞。

### Schema-First（Schema 优先）

- `schemas/screenplay.schema.json` 是前后端之间的**唯一真相源**。所有数据结构、字段类型、必填项、约束都在这里定义。
- Schema 不可再随意修改；任何修改 `schemas/` 下 schema assets 的行为，必须先说明改动原因、影响范围和兼容性风险，并得到用户明确审核通过后才能执行。
- 后端保证产出符合 schema 的数据；前端按 schema 解析和渲染，不自行推测字段含义。
- 改字段必须先从 schema 开始 → 再改 fixtures → 再改代码。不要跳过 schema 直接改代码。

### API Contract（接口契约）

- 前后端**只能通过 HTTP API 通信**。前端永远不直接 import 后端模块、不直接调后端函数。
- 所有请求/响应类型用 Pydantic DTO 定义在 `backend/app/api/dto/`，前端侧对应 `frontend/api_client.py` 封装所有 HTTP 调用。
- 前端 `api_client.py` 是前端访问后端的**唯一入口**——API path、请求体、错误处理全部集中在这里，不散落在 view 组件里。
- 后端路由只做参数校验和调度，不写 prompt、不直接操作数据库、不 repair content。

### Fake Provider（前端无需真实 AI）

- 设置 `XENGINEER_AI_PROVIDER=fake` 后，后端全流水线用**确定性假数据**运行，不调用任何外部 AI API。
- Fake Provider 优先读 `fixtures/projects/<项目名>/` 下的项目级 fixture；没有匹配 fixture 时根据当前章节动态构造项目相关假数据。
- **前端开发者不需要 API Key、不需要等 AI 返回、秒级跑通全流水线**，可以独立开发和调试 UI。
- Fake 和 Real provider 共享同一条 orchestrator path——fake 通了，换 real 只需要改环境变量。

### Normalization + Validation Pipeline（归一化 + 校验管道）

- **Normalizer**（`backend/app/validators/screenplay_normalizer.py`）：LLM 输出不可靠——可能缺字段、多 null、格式不对。归一化层在**校验之前**递归清洗数据：补全缺失字段、删除非法 null、对齐 schema 类型。不修业务内容，只修结构。
- **Validator**（`backend/app/validators/schema_validator.py`）：用 jsonschema 做精确结构校验，返回带 `path` + `schema_path` 的结构化 findings，方便前端定位问题。
- 校验结果写入 `audit_report`，前端可用 `ValidationFindingResponse` 展示给用户。
- 规则：**代码负责结构，AI 负责内容**。ID 生成、引用检查、格式校验属于后端；角色动机、对白创作属于 AI。

### Frontend State Management（前端状态管理）

- `frontend/utils/state.py` 统一管理 Streamlit session_state，所有页面状态在这里初始化，不散落在各 view。
- session 中持有 `backend_project_id`、`backend_job_id`、`backend_job_status`、`screenplay_data`、`rendered_markdown` 等后端联调快照，页面刷新不丢失。
- `frontend/utils/storage.py` 负责本地 `data/projects.json` 的持久化，含旧数据自动迁移逻辑。
- 前端项目创建时同时调用 `api_client.create_project()` 同步后端——后端不可用时保留本地项目，不阻塞首页流程。

### Fixture Contract（Fixtures 契约）

- `fixtures/` 只用于 demo、mock 和 contract 验证，**不是**真实项目运行时数据目录。
- 真实项目数据写入 `backend/data/projects/{project_id}/`，结构为 `project.json` + `chapters/index.json` + `artifacts/index.json` + `jobs/index.json`。
- 项目级 fixture 放在 `fixtures/projects/{safe_project_name}/`，Fake Provider 按项目标题/ID 匹配。

### Export Pipeline（导出管道）

- 内部统一用 JSON（校验、引用追踪、artifact 存储）。
- 导出走：`screenplay_json` → `YAML`（人可读编辑）+ `Rendered Text/Markdown`（文学剧本排版）。
- Exporter 只做格式转换，不 repair content、不补数据、不修改业务字段。
- YAML 导出含完整 `adaptation_config` 和 `adaptation_plan`。

## Code Commenting Convention（代码注释约定）

所有新增或修改的代码，都要保留 `backend/app/domain/` 及其 `description.md` 中已经形成的解释性风格：

- 新建 code file 时，在 file header 添加简短注释，说明该文件在 novel-to-screenplay pipeline 中的具体 responsibility。
- 在 large classes、large functions、orchestration steps、validation rules、exporters、provider adapters 或 non-obvious code blocks 前添加简短注释，说明这段代码 does what，以及 why it exists。
- 在已有文件中新增代码块时，如果仅靠命名和类型不能立刻看出目的，要说明局部原因和预期用途。
- 注释要 specific and operational，优先解释 business meaning、data flow、boundaries、invariants 和 failure behavior，不要复述 simple syntax。
- 删除代码时不要额外添加“这里删掉了什么”的 tombstone notes；obsolete code 应干净移除。

## Document and Output Language（文档和输出语言约定）

- 如果生成或修改的 Markdown 文件目的是给人阅读，面向用户的自然语言必须使用中文。
- English technical nouns、domain terms、role names、field names 和 architecture terms 应优先保留英文原词；需要中文说明时，用“中文说明 + English term”的方式，避免后续 Agent 看不懂对应关系。
- Machine contracts、test fixtures、schema、export examples、code identifiers、API field names、file paths 和 commands 可以保留英文或原始格式。
- 如果 Markdown 同时包含 machine-readable snippets 和 explanation text，explanation text 用中文，machine-readable snippets 保持其 contract format。

## Agent Team（Agent 团队）

- Showrunner：守住 V0+V1 范围，冻结 demo path，负责 gates。
- Contract Architect：负责 fixtures、schema、ID 规则、DTO/API contracts。
- Backend Builder：负责 FastAPI、domain、services、repositories、workers 和 export。
- Skill Engineer：负责 provider contracts、skill wrappers 和 prompt references。
- Validation Director：负责 schema/reference validation 和 audit warning mapping。
- Review Director：在 gates 给出 PASS/FAIL，并指出位置、问题和行动。
- Continuity Recorder：保护最小事件、伏笔和知识状态。
- Demo Producer：负责 smoke path、demo checklist 和冻结示例资产。

## Review Gates（评审门）

Gate 0 Scope：

- Changes 只服务 V0+V1。
- Future capabilities 只能通过 fields 或 directories 预留，不能提前实现。

Gate 1 Contract：

- Fixtures、schemas、Pydantic models、DTOs 和 frontend expectations 必须对齐。
- Field changes 必须先从 fixtures 开始，再改 code。

Gate 2 Backend Boundary：

- API 不 compose prompts。
- Skills 不 write database records。
- Validators 不 call models。
- Exporters 不 repair content。
- Services 负责 orchestrate；不要持有 large prompt bodies。

Gate 3 Artifact：

- Pipeline 每一步都要保存 artifact。
- Jobs expose status、current step、errors 和 artifact IDs。
- Fake provider 和 real provider 共享同一条 orchestrator path。

Gate 4 Validation：

- Broken references 必须被 deterministically detected。
- Warnings 必须指向具体 entity IDs。
- `fixtures/demo_invalid_refs.yaml` 必须触发预期 findings。

Gate 5 Demo：

- Smoke path 在没有 real API key 的情况下也能运行。
- YAML 可读、可解析、可下载。
- Demo 能解释 structured adaptation，而不是 black-box generation。

## Execution Order（执行顺序）

除非后续已有批准计划明确改动，否则按以下顺序推进：

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

实践规则：fixture first，domain second，validators third，fake provider fourth，orchestrator fifth，real provider last。

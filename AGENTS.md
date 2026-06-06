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

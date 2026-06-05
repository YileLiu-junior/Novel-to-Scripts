---
title: AI 小说转剧本 MVP 项目目录结构
status: draft
origin:
  - docs/plans/2026-06-05-001-architecture-ai-novel-to-script-plan.md
  - docs/plans/2026-06-05-003-phase-1-contract-model-api-schema.md
created: 2026-06-05
---

# AI 小说转剧本 MVP 项目目录结构

## 1. 总体原则

本项目建议采用前后端分离的轻量 monorepo：

```text
XEngineer/
  backend/      # Python + FastAPI，负责业务模型、AI workflow、校验、YAML 导出
  frontend/     # React + TypeScript + Vite，负责工作台 UI
  fixtures/     # 前后端共享 demo 数据和 mock 数据
  schemas/      # 对外 YAML/JSON Schema 文档和机器可读 schema
  docs/         # 方案、接口说明、Schema 说明、demo 脚本
  scripts/      # 本地开发、生成类型、数据检查、demo smoke 等辅助脚本
```

核心分工：

- `backend/` 是结构可信的中心。
- `frontend/` 是创作者工作台。
- `fixtures/` 是并行开发的握手文件。
- `schemas/` 是比赛/评审能看到的 Schema 资产。
- `docs/` 是产品和技术叙事。
- `scripts/` 只放跨项目工具，不放业务逻辑。

## 2. 推荐完整目录树

```text
XEngineer/
  README.md
  .gitignore
  .env.example

  backend/
    README.md
    pyproject.toml
    .env.example
    app/
      __init__.py
      main.py

      core/
        __init__.py
        config.py
        errors.py
        ids.py
        logging.py

      api/
        __init__.py
        router.py
        routes_projects.py
        routes_chapters.py
        routes_generation.py
        routes_artifacts.py
        routes_jobs.py
        routes_yaml.py
        routes_schema.py
        routes_health.py
        dto/
          __init__.py
          projects.py
          chapters.py
          generation.py
          artifacts.py
          jobs.py
          validation.py
          yaml.py
          schema.py

      domain/
        __init__.py
        common.py
        project.py
        source.py
        story_bible.py
        adaptation.py
        screenplay.py
        audit.py
        artifacts.py
        jobs.py
        llm_runs.py

      db/
        __init__.py
        session.py
        tables.py
        migrations/

      repositories/
        __init__.py
        project_repository.py
        chapter_repository.py
        artifact_repository.py
        job_repository.py
        llm_run_repository.py

      services/
        __init__.py
        project_service.py
        chapter_service.py
        artifact_service.py
        generation_orchestrator.py
        job_service.py
        yaml_service.py
        schema_service.py
        validation_service.py
        llm_trace_service.py

      validators/
        __init__.py
        reference_validator.py
        schema_validator.py
        chapter_validator.py
        audit_validator.py

      ai/
        __init__.py
        providers/
          __init__.py
          base.py
          fake_provider.py
          openai_provider.py
        skills/
          __init__.py
          novel_reader.py
          story_ontology.py
          adaptation_planner.py
          screenplay_writer.py
          dialogue_doctor.py
          continuity_auditor.py
        prompts/
          novel_reader.md
          story_ontology.md
          adaptation_planner.md
          screenplay_writer.md
          dialogue_doctor.md
          continuity_auditor.md

      workers/
        __init__.py
        jobs.py

      exporters/
        __init__.py
        yaml_exporter.py
        schema_exporter.py

    tests/
      conftest.py
      api/
        test_chapters_api.py
        test_generation_api.py
        test_yaml_api.py
      services/
        test_chapter_service.py
        test_yaml_service.py
        test_generation_orchestrator.py
      validators/
        test_reference_validator.py
        test_schema_validator.py
      ai/
        test_fake_provider.py
        test_skill_contracts.py

  frontend/
    README.md
    package.json
    tsconfig.json
    vite.config.ts
    index.html
    public/
      favicon.svg
    src/
      main.tsx
      app/
        App.tsx
        providers.tsx
        routes.tsx
      api/
        client.ts
        endpoints.ts
        types.ts
        mock-client.ts
      state/
        workbench-store.ts
      features/
        project/
          ProjectShell.tsx
        chapters/
          ChapterEditor.tsx
          ChapterList.tsx
          ChapterStats.tsx
        generation/
          GenerationProgress.tsx
          GenerationActions.tsx
        story-bible/
          StoryBiblePanel.tsx
          CharacterCard.tsx
          RelationshipList.tsx
          KnowledgeStateList.tsx
          EventList.tsx
          ForeshadowingList.tsx
        adaptation/
          AdaptationConfigPanel.tsx
          AdaptationPlanView.tsx
        screenplay/
          SceneList.tsx
          SceneDetail.tsx
          DialoguePanel.tsx
          SourceRefsPanel.tsx
        audit/
          AuditPanel.tsx
          WarningList.tsx
        export/
          YamlPreviewEditor.tsx
          ExportActions.tsx
      components/
        layout/
          WorkbenchLayout.tsx
          Sidebar.tsx
          InspectorPanel.tsx
        ui/
          Button.tsx
          Card.tsx
          Tabs.tsx
          Select.tsx
          CheckboxGroup.tsx
          Badge.tsx
          EmptyState.tsx
          ErrorState.tsx
      styles/
        globals.css
      test/
        setup.ts

  fixtures/
    demo_novel_3_chapters.json
    demo_story_bible.json
    demo_screenplay.json
    demo_screenplay.yaml
    demo_audit_report.json
    demo_invalid_refs.yaml

  schemas/
    screenplay.schema.json
    screenplay.schema.yaml
    screenplay-schema-design.md
    openapi.snapshot.json

  docs/
    plans/
    api/
      api-contract.md
    demo/
      demo-script.md
      demo-checklist.md
    schema/
      screenplay-schema-explained.md

  scripts/
    export_openapi.py
    validate_fixtures.py
    generate_frontend_types.py
    run_demo_smoke.py
```

## 3. 后端目录职责

### `backend/app/domain/`

放 Pydantic 领域模型，是项目的“内部真相源”。

建议拆分：

- `common.py`：`SourceRef`、枚举、基础 ID 类型。
- `source.py`：`Chapter`、`Paragraph`。
- `story_bible.py`：`Character`、`RelationshipEdge`、`KnowledgeState`、`VoiceProfile`。
- `adaptation.py`：`AdaptationConfig`、`AdaptationPlan`、`ScenePlan`。
- `screenplay.py`：`Scene`、`DialogueLine`、`Location`。
- `audit.py`：`AuditReport`、`AuditWarning`。
- `artifacts.py`：`Artifact` 类型。
- `jobs.py`：`GenerationJob` 状态。
- `llm_runs.py`：每次模型调用的追踪记录，包括 prompt version、provider、raw/parsed output 和 validation errors。

### `backend/app/api/`

放 FastAPI 路由和请求/响应 DTO。

路由与业务对应：

- `routes_projects.py`：创建/读取项目。
- `routes_chapters.py`：保存章节、自动拆章、3 章校验。
- `routes_generation.py`：触发 story bible、adaptation plan、screenplay、audit 生成。
- `routes_artifacts.py`：读取每一步 artifact。
- `routes_jobs.py`：查询 job 状态和阶段错误。
- `routes_yaml.py`：YAML 预览、校验、下载。
- `routes_schema.py`：Schema 下载。
- `routes_health.py`：健康检查。

API 层只做参数解析、权限/输入边界和响应 DTO，不直接调用模型，不直接读写数据库。

### `backend/app/db/` 与 `backend/app/repositories/`

`db/` 放数据库连接、表定义和迁移入口；`repositories/` 放持久化读写。

MVP 用 SQLite，也仍然建议保留 repository 层，原因是：

- 生成流程会频繁保存 `artifact`、`job`、`llm_run`，直接散落在 service 中后期很难重试。
- 未来从 SQLite 切到 PostgreSQL JSONB 时，service 和 API 不应该重写。
- `FakeProvider` 与真实模型都要能写入同一套 artifact，方便 demo 和调试复用。

### `backend/app/ai/`

放 AI 相关实现。

分三层：

- `providers/`：真实或假的模型调用器。
- `skills/`：每个 skill 的 Python wrapper，只负责把结构化输入转成 prompt，再把模型响应解析成结构化输出。
- `prompts/`：每个 skill 的 prompt 文本。

第一阶段先实现：

- `providers/fake_provider.py`
- `skills/novel_reader.py`
- `skills/story_ontology.py`
- `skills/adaptation_planner.py`
- `skills/screenplay_writer.py`

真实模型后面再接，不要一开始卡在 API key 和输出不稳定上。

AI 层不要保存数据库，也不要生成最终 YAML。它只返回候选结构；持久化、校验、导出交给 service / validator / exporter。

### `backend/app/services/`

放业务编排，不直接写 API 细节。

关键服务：

- `generation_orchestrator.py`：串联所有 skill。
- `validation_service.py`：聚合引用校验和 Schema 校验。
- `yaml_service.py`：JSON/Pydantic -> YAML。
- `schema_service.py`：导出 Schema 文档。
- `chapter_service.py`：章节拆分、段落编号、字数统计。
- `llm_trace_service.py`：记录 prompt version、model、raw output、parsed output、token/latency 和 validation errors。

`generation_orchestrator.py` 是 V1 后端最重要的文件之一，但它不应该变成巨大的 prompt 文件。它只负责串联：

```text
load artifacts -> call skill -> validate -> save artifact -> update job
```

每个阶段都应该可单独重试。

### `backend/app/validators/`

放更细的校验器，避免 `validation_service.py` 变成一个巨大文件。

- `reference_validator.py`：检查 `char_001`、`event_001`、`scene_001` 是否存在。
- `schema_validator.py`：检查字段、类型、必填项。
- `chapter_validator.py`：检查至少 3 章、章节顺序、空文本。
- `audit_validator.py`：把校验问题转成 `AuditWarning`。

校验器必须是确定性的纯逻辑，不调用模型。这样 demo 失败时可以判断是结构问题、引用问题，还是模型质量问题。

### `backend/app/workers/`

V1 可以先用 FastAPI `BackgroundTasks`，但仍然保留 `workers/jobs.py`：

- 当前实现：把生成任务包装成后台函数，写入 `generation_jobs`。
- 后续升级：迁移到 RQ/Celery + Redis 时，API 和 service 调用口径不变。

不要在 V1 引入 Redis 队列；只把目录和边界留出来。

### `backend/app/exporters/`

放纯导出逻辑：

- `yaml_exporter.py`：把已验证的内部 JSON/Pydantic 结构序列化为 YAML。
- `schema_exporter.py`：把 Pydantic/JSON Schema 和说明文档导出给评审或前端下载。

`exporters/` 不做业务判断，不补字段，不修复模型输出。修复应该发生在 validator 或 repair skill 阶段。

### `backend/tests/`

测试目录放在 `backend/tests/`，不要放进 `backend/app/`。这样 `app/` 保持为运行时代码，测试可以按 API、service、validator、AI contract 分层。

第一阶段至少覆盖：

- 2 章失败、3 章通过。
- `FakeProvider` 能跑完整 generation job。
- 引用不存在的 `character_id` / `event_id` 能产生 warning 或 error。
- YAML 导出后可以重新解析并校验。
- skill wrapper 输出缺字段时，job 状态变为 `failed`，并保留错误信息。

## 4. 前端目录职责

### `frontend/src/features/`

按业务模块拆，不按技术类型拆。

这样你们后面看代码时能直接对应产品页面：

- `chapters/`：导入小说。
- `story-bible/`：故事圣经。
- `adaptation/`：改编策略。
- `screenplay/`：剧本场景与台词。
- `audit/`：审查 warning。
- `export/`：YAML 预览和下载。

### `frontend/src/api/`

前后端对接层。

- `client.ts`：真实 API client。
- `mock-client.ts`：读取 fixtures 的 mock client。
- `types.ts`：前端类型，第一阶段可以手写，后续可从 OpenAPI 生成。
- `endpoints.ts`：统一管理 API 路径。

第一阶段前端默认接 `mock-client.ts`，等后端接口稳定后切到 `client.ts`。

### `frontend/src/components/`

只放通用 UI，不放业务逻辑。

业务组件都放在 `features/`，避免后期 `components/` 变成杂物间。

## 5. 共享目录职责

### `fixtures/`

这是两人并行开发最重要的目录。

建议第一阶段先写：

- `demo_novel_3_chapters.json`：原始 3 章小说输入。
- `demo_story_bible.json`：故事圣经 mock。
- `demo_screenplay.json`：内部 JSON 真相源 mock。
- `demo_screenplay.yaml`：最终导出展示 mock。
- `demo_audit_report.json`：审查 warning mock。
- `demo_invalid_refs.yaml`：故意包含断裂引用，用来验证校验器和前端 warning 展示。

fixture 不是一次性样例，而是前后端共同遵守的契约测试资产。字段改动必须先改 fixture，再改模型、API 和前端类型。

### `schemas/`

这里放“契约资产”，不是后端代码。

- `screenplay.schema.json`：机器可读 Schema。
- `screenplay.schema.yaml`：YAML 版本 Schema。
- `screenplay-schema-design.md`：给评审看的 Schema 设计说明。
- `openapi.snapshot.json`：后端导出的 API 快照。

### `docs/`

放设计文档和交付材料。

- `docs/plans/`：技术方案和排期。
- `docs/api/`：接口说明。
- `docs/schema/`：Schema 解释文档。
- `docs/demo/`：demo 脚本和彩排清单。

## 6. 第一阶段最小可建目录

如果你们现在要开工，不必一次建完整目录。先建这版最小目录：

```text
XEngineer/
  backend/
    app/
      main.py
      api/
      domain/
      db/
      repositories/
      services/
      ai/
        providers/
        skills/
        prompts/
      validators/
      workers/
      exporters/
    tests/

  frontend/
    src/
      app/
      api/
      features/
      components/
      state/
      styles/

  fixtures/
    demo_novel_3_chapters.json
    demo_story_bible.json
    demo_screenplay.json
    demo_screenplay.yaml
    demo_audit_report.json
    demo_invalid_refs.yaml

  schemas/
    screenplay.schema.json
    screenplay.schema.yaml
    screenplay-schema-design.md

  docs/
    plans/
    api/
    demo/

  scripts/
    validate_fixtures.py
    run_demo_smoke.py
```

这已经够支撑第一阶段：

```text
Pydantic 模型
  -> API skeleton
  -> fake provider
  -> fixture 联调
  -> YAML 导出和校验
```

## 7. 不建议的目录方式

不建议把所有 AI 逻辑放到一个 `ai.py`。

原因：

- 后期 skill 会越来越多。
- prompt、provider、wrapper 混在一起会很难调。

不建议前端按 `pages/components/utils` 粗暴三分。

原因：

- 这个产品是工作台，业务模块强。
- `features/chapters`、`features/story-bible` 这种拆法更容易多人并行。

不建议把 fixture 放到 `frontend/` 或 `backend/` 里面。

原因：

- fixture 是共享契约。
- 放某一端会让另一端看起来像“借用数据”，协作上容易跑偏。

## 8. 推荐开工顺序

第一步建共享目录：

```text
fixtures/
schemas/
docs/api/
docs/demo/
```

第二步后端建：

```text
backend/app/domain/
backend/app/api/
backend/app/db/
backend/app/repositories/
backend/app/ai/providers/
backend/app/ai/skills/
backend/app/services/
backend/app/validators/
backend/app/workers/
backend/app/exporters/
```

第三步前端建：

```text
frontend/src/api/
frontend/src/features/chapters/
frontend/src/features/story-bible/
frontend/src/features/adaptation/
frontend/src/features/screenplay/
frontend/src/features/audit/
```

这样不会一开始就陷入工程脚手架细节，同时能保证前后端按照同一套契约推进。

## 9. V1 工程边界检查

开工后用这组规则防止目录变形：

1. `domain/` 只定义 Pydantic 类型和枚举，不 import FastAPI、SQLAlchemy、OpenAI SDK。
2. `api/` 只处理 HTTP 输入输出，不直接拼 prompt，不直接写 YAML。
3. `ai/skills/` 只做 skill wrapper，不保存数据库，不决定 job 状态。
4. `services/` 负责业务流程和阶段编排，可以依赖 repository、validator、skill。
5. `validators/` 必须可在无模型、无数据库的情况下单独测试。
6. `exporters/` 只导出，不补字段，不悄悄修复内容。
7. `fixtures/` 是前后端和测试的共同契约，不能只为前端展示服务。
8. `workers/` V1 只做后台任务包装，Redis/Celery 是未来替换点，不是当前依赖。

## 10. 最小验收路径

目录结构落地后，第一条 smoke path 应该是：

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

这条路径跑通后，真实模型接入只是替换 provider 和 prompt，不需要推翻目录结构。

---
date: 2026-06-06
topic: backend-storyontology-adaptation-evidence
status: planned
origin: docs/specs/backend-StoryOntology/01-adaptation-evidence-requirements.md
---

# StoryOntology V1.5 执行计划

## Summary

本计划把 StoryOntology V1.5 做成 contract-first 的 `Adaptation Evidence` artifact 增强：先扩展 schema 和 fixtures，再更新 domain、fake provider、prompt、orchestrator normalization、validator、frontend 展示和 tests。主 `/generate/screenplay` pipeline 保持不变。

---

## Problem Frame

当前系统已经有 `StoryOntologySkill`、`story_bible` artifact 和结果页角色展示，但 evidence 没有成为用户可见的生成依据。直接增加 prompt 字段会形成 shadow contract，也无法保证 planner、validator 和 frontend 真正消费这些字段。

这次工作需要小步增强，而不是扩大成分步工作台。实现重点是让输入可声明、输出可追踪、artifact 可审查、断链可校验，同时不破坏 V0+V1 的 stable structured generation。

---

## Requirements Traceability

- 覆盖 `01-adaptation-evidence-requirements.md` 中的 R1-R14。
- 保留 `AGENTS.md` 中 Schema-first、API Contract、Fake Provider、Validation、Fixture Contract 和 Export Pipeline 约束。
- 复用 `.tmp-novel-to-script-team` 中适合 V0+V1 的约束：冲突提取、一致性锚点、称呼规范、完整事件原则。
- 排除长集数生产、付费卡点、分镜、生图和 hit-script retrieval flows。

---

## Key Technical Decisions

### D1. 开关放入 `adaptation_config`

使用 optional `adaptation_evidence_mode`，而不是新增独立 route 或独立 request body branch。

原因：

- 生成输入和最终 `screenplay_json.adaptation_config` 都能证明用户启用了 evidence。
- 不改变主 API path。
- `schemas/screenplay.schema.json` 的 `adaptation_config.additionalProperties` 已允许扩展。

### D2. 不新增独立主 contract

优先扩展 `schemas/screenplay.schema.json` 中现有 `story_bible` 和 `event` definitions。若后续添加 artifact helper schema，也必须从属于主 schema。

原因：

- `AGENTS.md` 明确 `screenplay.schema.json` 是唯一真相源。
- 前端不应在多个 schema 之间推测字段含义。

### D3. Evidence 保持 source-grounded

StoryOntology 输出描述性 facts，planner 输出改编决策。

允许 StoryOntology 标记：

- `complete_event`
- `event_flow`
- `must_keep_together`
- `conflict_axis`
- `continuity_anchors`
- `filmic_constraints`

不允许 StoryOntology 输出：

- retained/merged/deleted/deferred decisions
- episode plan
- screenplay scenes

### D4. 最小 planner 消费只做完整事件保护

V1.5 不追求 planner 全面理解所有 evidence，只要求 `must_keep_together` 被 scene plan 或 audit warning 体现。

原因：

- 避免 enriched fields 变成纯展示 metadata。
- 消费点小，容易测试。

---

## Implementation Units

### U1. Schema 和 fixture contract

**Files**

- `schemas/screenplay.schema.json`
- `schemas/screenplay.schema.yaml`
- `fixtures/demo_story_bible.json`
- `fixtures/demo_screenplay.json`
- `fixtures/projects/贝克街合租/demo_story_bible.json`
- `fixtures/projects/贝克街合租/demo_screenplay.json`
- 新增 `fixtures/demo_story_bible_invalid_refs.json`

**Work**

- 在 `adaptation_config` 中增加 optional `adaptation_evidence_mode`。
- 在 `story_bible` 中增加 optional `continuity_anchors` 和 `dramatic_assets`。
- 在 `event` definition 中增加 optional `complete_event`、`event_flow`、`must_keep_together`、`conflict_axis`。
- 更新 valid fixtures，让 demo 展示完整事件、冲突轴、一致性锚点和影视化约束。
- 新增 invalid fixture，包含不存在的 character/event/chapter 引用。

**Test scenarios**

- Given enriched fixture，schema validation 通过。
- Given old fixture，schema validation 仍通过。
- Given invalid fixture，reference validation 产生预期 findings。

---

### U2. Domain model optional fields

**Files**

- `backend/app/domain/adaptation.py`
- `backend/app/domain/story_bible.py`
- `backend/app/domain/description.md`

**Work**

- `AdaptationConfig` 增加 optional `adaptation_evidence_mode`，默认 `enabled`。
- `StoryBible` 增加 optional evidence fields 对应的 Pydantic models。
- `Event` 增加完整事件字段。
- 更新 `description.md`，说明 StoryOntology 是改编证据层，不是改编决策层。

**Test scenarios**

- Pydantic model 能 parse enriched fixture。
- Pydantic model 能 parse legacy minimal shape。
- `adaptation_evidence_mode` 缺失时默认启用。

---

### U3. StoryOntology prompt reference

**Files**

- `backend/app/ai/prompts/story_ontology.md`
- `docs/specs/backend-StoryOntology/04-storyontology-skill-prompt-reference.md`

**Work**

- 将 prompt 从 minimal story bible 升级为 Adaptation Evidence。
- 明确输入来自 `NovelReaderSkill` 的 `novel_analysis`。
- 明确输出 shape、ID 规则、完整事件原则、source_refs 规则和禁止事项。
- 明确不能生成 scenes，不能决定 retained/merged/deleted/deferred。

**Test scenarios**

- Prompt reference 中的 example JSON 能被 schema 接受。
- DeepSeek smoke 的 StoryOntology step 至少返回 dict，缺字段时 orchestrator 可降级或报错。

---

### U4. Fake provider enriched output

**Files**

- `backend/app/ai/providers/fake_provider.py`

**Work**

- 在 `adaptation_evidence_mode=enabled` 时输出 V1.5 enriched story assets。
- 在 `minimal` 时保留当前最小 shape。
- Fake output 必须继续基于当前项目章节动态生成，不回退到全局 demo。
- 项目级 fixture 优先级保持不变。

**Test scenarios**

- Fake provider 对相同章节输出 deterministic enriched evidence。
- Fake provider 在 `minimal` 模式下不输出 V1.5 sections。
- 项目级 fixture 存在时继续优先读取 fixture。

---

### U5. Orchestrator normalization 和 artifact metadata

**Files**

- `backend/app/services/generation_orchestrator.py`
- `backend/app/services/artifact_service.py`（只在需要 artifact ID mapping 时触碰）
- `backend/app/domain/artifacts.py`（只在类型或 metadata 需要时触碰）

**Work**

- `StoryOntologySkill.run` 输入加入 `adaptation_config`，让 provider 能读取 `adaptation_evidence_mode`。
- 保存 `story_bible` artifact 时保留 `schema_version`、`adaptation_evidence_mode`、`generated_by_skill` 和 `input_artifact_type`。
- 将 enriched `story_bible` 和 enriched `events` 注入最终 `screenplay_json`。
- 保持主 pipeline 顺序不变。

**Test scenarios**

- `/generate/screenplay` 成功后 artifact list 包含 enriched `story_bible`。
- Job 仍有 `current_step=story_ontology`。
- 旧模式或 `minimal` 模式不影响 screenplay JSON/YAML 导出。

---

### U6. Minimal planner/audit consumption

**Files**

- `backend/app/ai/providers/fake_provider.py`
- `backend/app/services/generation_orchestrator.py`
- `backend/app/validators/audit_validator.py` 或新增专门 validator（按现有 pattern 决定）
- `backend/app/services/validation_service.py`

**Work**

- Planner 输入包含 enriched events。
- Fake adaptation planner 对 `complete_event=true` 且 `must_keep_together=true` 的 event 保持同一个 `scene_plan[].source_events` 单元。
- 若 scene plan 无法体现该完整事件约束，产生 audit warning。

**Test scenarios**

- Given must-keep event，fake planner 的 scene plan 不拆散该 event。
- Given 人为构造的拆散 plan，audit report 包含完整事件 warning。
- Warning 指向具体 `event_id`。

---

### U7. Reference validation

**Files**

- `backend/app/validators/reference_validator.py`
- `backend/app/validators/schema_validator.py`（通常不需要改，除非新增 helper）
- `backend/tests/test_api_smoke_flow.py`
- 新增或扩展 validator tests

**Work**

- 检查 continuity anchors 的 character/chapter 引用。
- 检查 conflict pool 的 participants 和 related_events。
- 检查 filmic constraints 的 related_characters 和 related_events。
- 检查 `event_flow` 为 string array。

**Test scenarios**

- Missing character in anchor 返回 finding。
- Missing event in conflict pool 返回 finding。
- Missing chapter in source_refs 返回 finding。
- `event_flow` 非数组时 schema validation 返回 path 和 schema_path。

---

### U8. Frontend artifact-native display

**Files**

- `frontend/api_client.py`
- `frontend/backend_types.py`
- `frontend/views/export.py`
- `frontend/views/characters.py`（只修关系字段兼容时触碰）
- `frontend/utils/state.py`
- `frontend/utils/storage.py`

**Work**

- 前端通过 `api_client.get_artifact(project_id, "story_bible")` 拉取 evidence artifact。
- local/session state 保存 `story_bible_artifact` 或 `adaptation_evidence` 快照。
- 结果页新增或重命名 tab 为“改编证据”。
- 展示完整事件、冲突轴、一致性锚点、影视化约束、关系与知情差。
- 修正 relationship table 读取 `from` 和 `to`，兼容旧字段。
- 旧 artifact 缺失 enriched sections 时显示空态。

**Test scenarios**

- Given enriched artifact，结果页展示完整事件和 anchors。
- Given legacy artifact，页面不报错。
- Relationship row 使用 `from/to` 正确展示角色名。
- API path 只出现在 `frontend/api_client.py`。

---

### U9. YAML/export stability

**Files**

- `backend/app/exporters/yaml_exporter.py`
- `backend/app/services/yaml_service.py`
- `fixtures/demo_screenplay.yaml`

**Work**

- 确认 exporter 不合成 evidence。
- 如果 `screenplay_json.story_bible` 已含 enriched fields，YAML 自然包含；否则不补。
- 更新 demo YAML 只跟随 fixture/schema，不写 exporter repair logic。

**Test scenarios**

- Enriched screenplay YAML 可 parse。
- YAML 中仍包含完整 `adaptation_config` 和 `adaptation_plan`。
- Exporter 不因旧 story_bible 缺 enriched fields 失败。

---

### U10. Documentation and acceptance smoke

**Files**

- `docs/specs/backend-StoryOntology/README.md`
- `docs/specs/backend-StoryOntology/01-adaptation-evidence-requirements.md`
- `docs/specs/backend-StoryOntology/02-adaptation-evidence-contract.md`
- `docs/specs/backend-StoryOntology/03-implementation-plan.md`
- `docs/specs/backend-StoryOntology/04-storyontology-skill-prompt-reference.md`
- `BACKEND_UNIMPLEMENTED_VERSION_MAP.md`
- `fixtures/前端接入指南.md`（如需同步前端说明）
- `fixtures/后端说明文档和路径情况.md`（如需同步后端说明）

**Work**

- 记录 StoryOntology V1.5 是主链路增强，不是独立生成流程。
- 更新未实现清单，把独立 `/generate/story-bible` 继续标记为后续项。
- 更新接入指南，说明 `adaptation_evidence_mode` 和结果页 evidence artifact。

**Test scenarios**

- 文档中没有宣称会实现 non-goals。
- 文档引用路径全部是 repo-relative。
- 前后端说明与 API 实际行为一致。

---

## Dependency Order

```text
U1 schema + fixtures
  -> U2 domain
  -> U3 prompt reference
  -> U4 fake provider
  -> U5 orchestrator artifact metadata
  -> U6 planner/audit minimal consumption
  -> U7 reference validation
  -> U8 frontend display
  -> U9 YAML/export stability
  -> U10 documentation sync
```

## Verification Plan

建议最小验证命令：

```text
python scripts/validate_fixtures.py
pytest backend/tests/test_api_smoke_flow.py
pytest backend/tests/test_screenplay_normalizer.py
pytest backend/tests/ai/test_ai_providers.py
```

如新增 validator tests，应单独运行对应 test file。

前端验证：

- 启动后端 fake provider。
- 导入至少三章。
- 点击生成。
- 检查 job step 出现 `story_ontology`。
- 进入结果页，确认“改编证据”能展示 enriched sections。

## Risks

- 字段过多导致假复杂：本计划只保留完整事件、冲突轴、一致性锚点和影视化约束。
- Optional fields 腐化：用 fixtures、schema、domain 和 tests 固化 contract。
- StoryOntology 越界做规划：文档和 prompt 明确 retained/merged/deleted/deferred 只能由 planner 输出。
- 旧 artifact 兼容：前端和 planner 必须把缺失 sections 当空值处理。
- Exporter 被误用来 repair：U9 明确禁止 exporter 合成或修复 evidence。

## Deferred to Follow-Up Work

- 接通独立 `/generate/story-bible` route。
- StoryOntology artifact 编辑和人工确认。
- 更丰富的 planner 消费策略。
- 长集数 episode planning、付费卡点和 retention beats。
- AI continuity auditor 或 dialogue doctor 回路。

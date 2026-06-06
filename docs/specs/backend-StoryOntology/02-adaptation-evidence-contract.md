# StoryOntology V1.5 规则与输入输出 Contract

## 目标

`StoryOntologySkill` 的 V1.5 输出不再只是“角色列表 + 关系 + 知情状态”，而是面向后续 planner、validator 和前端结果页的 `Adaptation Evidence`。它回答三个问题：

1. 原文中有哪些必须被保护的叙事事实？
2. 哪些事件是完整事件，不能被无依据拆碎？
3. 后续 scene plan 和 screenplay 如何追溯回这些事实？

## Backend 开关

新增一个后端可见输入字段：

```json
{
  "adaptation_config": {
    "target_format": "web_series",
    "fidelity_level": "high",
    "preserve_priorities": ["relationship_arc", "foreshadowing"],
    "dialogue_style": "restrained_with_subtext",
    "adaptation_evidence_mode": "enabled"
  }
}
```

### 字段规则

- `adaptation_evidence_mode` 是 optional field。
- 允许值：
  - `enabled`：默认值，StoryOntology 输出 V1.5 evidence。
  - `minimal`：保留现有最小 story bible 输出，仅用于 backend/debug/legacy compatibility，例如兼容旧 demo 或定位问题。
- 不提供 `off`：StoryOntology 是 V1 pipeline 必经步骤，不能通过开关绕过。
- 该字段进入 `adaptation_config`，让输入和最终 `screenplay_json.adaptation_config` 都能证明 StoryOntology evidence 已启用。
- 正常用户界面不暴露 `minimal` 选择器；前端可以不传该字段，或固定传入 `enabled`。

## Artifact 输出形态

`story_bible` artifact 仍保存为 artifact type `story_bible`，但 data 使用 V1.5 shape：

```json
{
  "schema_version": "story_ontology_evidence_1.5",
  "adaptation_evidence_mode": "enabled",
  "generated_by_skill": "story_ontology",
  "input_artifact_type": "novel_analysis",
  "story_bible": {
    "characters": [],
    "relationship_edges": [],
    "knowledge_states": [],
    "continuity_anchors": [],
    "dramatic_assets": {
      "conflict_pool": [],
      "filmic_constraints": []
    }
  },
  "events": [],
  "causal_graph": {
    "edges": []
  },
  "foreshadowing": []
}
```

## Schema-first 约束

`schemas/screenplay.schema.json` 仍是前后端唯一主 contract。V1.5 应在现有对象中增加 optional fields：

- `story_bible.continuity_anchors`
- `story_bible.dramatic_assets`
- `events[].complete_event`
- `events[].event_flow`
- `events[].must_keep_together`
- `events[].conflict_axis`

不要新增与主 contract 竞争的独立真相源。若后续需要 `schemas/story_bible.schema.json`，它只能作为 artifact 级辅助校验，不得替代 `screenplay.schema.json`。

## 新字段定义

### `story_bible.continuity_anchors`

用于记录不可漂移的一致性锚点。

建议 shape：

```json
{
  "id": "anchor_001",
  "anchor_type": "addressing_rule",
  "summary": "华生称呼福尔摩斯为福尔摩斯，不使用亲昵称呼。",
  "applies_to": ["char_001", "char_002"],
  "source_refs": [{"chapter_id": "chapter_001", "paragraph_range": "p_002-p_003"}]
}
```

允许 `anchor_type`：

- `addressing_rule`
- `character_trait`
- `relationship_state`
- `object`
- `timeline`
- `world_rule`

### `story_bible.dramatic_assets.conflict_pool`

用于记录原文中已经存在的 source-grounded conflict，不直接生成爽点或改编决策。

建议 shape：

```json
{
  "id": "conflict_001",
  "conflict_axis": "好奇与隐瞒",
  "participants": ["char_001", "char_002"],
  "related_events": ["event_002"],
  "source_refs": [{"chapter_id": "chapter_002"}]
}
```

### `story_bible.dramatic_assets.filmic_constraints`

用于记录“必须转化为可演、可见、可听表达”的原文信息。该字段名保持 `filmic_constraints` 以降低 contract churn，但面向用户的展示名统一为“可视化表达约束”。

建议 shape：

```json
{
  "id": "filmic_001",
  "constraint_type": "internal_state_to_action",
  "summary": "华生的不安不能只用旁白说明，需要通过观察、停顿或动作表现。",
  "related_characters": ["char_001"],
  "related_events": ["event_001"],
  "source_refs": [{"chapter_id": "chapter_001"}]
}
```

### `events[]` enriched fields

每个 event 可增加：

```json
{
  "complete_event": true,
  "event_flow": ["寻找住处", "被介绍合租者", "听到风险提醒", "决定见面"],
  "must_keep_together": true,
  "conflict_axis": "安顿需求 vs 合租风险"
}
```

规则：

- `complete_event` 表示事件具有明确开始、发展和结果。
- `event_flow` 必须按原文事件顺序记录连续动作，不写改编后的 scene。
- `must_keep_together` 表示 planner 不应把连续动作无依据拆散。
- `conflict_axis` 描述原文内已存在的冲突，不创造新冲突。

## StoryOntology 和 AdaptationPlanner 的边界

StoryOntology 负责：

- 描述角色、关系、知情差、事件、因果、伏笔。
- 描述 source-grounded conflict 和 continuity anchors。
- 标记完整事件和连续动作。
- 输出可被 planner 消费的 evidence。

StoryOntology 不负责：

- 决定 retained、merged、deleted、deferred。
- 设计 episode 数、付费卡点、长剧集结构。
- 生成 screenplay scenes。
- repair LLM 输出。

AdaptationPlanner 负责：

- 根据 evidence 和 `adaptation_config` 生成 `adaptation_plan`。
- 决定保留、合并、删除或延后事件。
- 生成 scene plan。
- 对 `must_keep_together` 给出规划层响应。

## 最小 planner 消费规则

V1.5 只要求一个可测试的消费点：

> 如果一个 event 同时满足 `complete_event=true` 和 `must_keep_together=true`，planner 不应把该 event 的连续动作拆到多个互不相连的 scene plan item。若无法满足，应写入 audit warning。

该规则不要求 planner 完美生成内容，只要求它尊重 StoryOntology 给出的完整事件约束。

前端展示时应把该消费点转成用户可理解的状态，而不是只把 warning 藏在 audit report：

- `已保护`：event 出现在 `adaptation_plan.scene_plan[*].source_events` 中，且没有被拆散到多个互不相连的 scene plan item。
- `被拆分需说明`：`must_keep_together=true` 的 event 被拆到多个 scene plan item，且缺少明确 justification。
- `未关联场景`：event 没有出现在任何 `scene_plan[*].source_events` 中。

## Validation 规则

Deterministic validation 只检查结构和引用：

- `continuity_anchors[].applies_to[]` 必须引用存在的 character ID。
- `continuity_anchors[].source_refs[].chapter_id` 必须存在。
- `conflict_pool[].participants[]` 必须引用存在的 character ID。
- `conflict_pool[].related_events[]` 必须引用存在的 event ID。
- `filmic_constraints[].related_characters[]` 必须引用存在的 character ID。
- `filmic_constraints[].related_events[]` 必须引用存在的 event ID。
- `events[].event_flow` 如果存在，必须是非空 string array。

Validation 不检查：

- 冲突是否精彩。
- 角色动机是否高级。
- event_flow 是否有商业爆点。
- `filmic_constraints` 是否有最佳拍法。

## Export 规则

- 内部仍统一使用 JSON artifact。
- YAML export 仍走 `screenplay_json -> YAML`。
- Exporter 不补 evidence、不 repair evidence、不根据 evidence 改写业务字段。
- 如果 `screenplay_json.story_bible` 包含 V1.5 optional fields，YAML 可以自然包含它们；不要在 exporter 中临时合成。

## Frontend 展示规则

前端展示名称建议：

- 主 tab：`改编证据`
- 子区块：`完整事件`、`冲突轴`、`一致性锚点`、`关系与知情差`、`可视化表达约束`、`伏笔追踪`

展示策略：

- 优先展示 `story_bible` artifact 中的 evidence。
- artifact 缺失时，退回 `screenplay_json.story_bible`。
- 旧 artifact 缺少 V1.5 字段时显示空态，不报错。
- 所有 API 调用集中在 `frontend/api_client.py`。
- 场景卡片应提供最小 `scene-to-evidence trace`，从 scene 追溯到关联 event、conflict axis、source refs 和 continuity anchor。
- `可视化表达约束` 区块需要说明：这里不是拍摄指导或镜头设计，只指出小说信息中哪些内容必须被转化为可演、可见、可听的表达。

## 兼容规则

- 旧 `story_bible` artifact 没有 `schema_version` 时视为 `legacy_minimal`。
- `adaptation_evidence_mode` 缺失时视为 `enabled`，但前端应显示“旧数据未声明模式”或直接隐藏模式说明。
- `minimal` 模式仍保存 `story_bible`、`events`、`causal_graph`、`foreshadowing`，只是不输出 V1.5 enriched fields；该模式不作为正常用户配置项。

---
title: AI 小说转剧本 MVP 第一阶段契约设计
status: active
origin:
  - Pre-research/AI小说转剧本MVP方案细化.md
  - docs/plans/2026-06-05-001-architecture-ai-novel-to-script-plan.md
  - docs/plans/2026-06-05-002-ai-novel-to-script-2-person-timeline.md
  - thread:019e93d5-2fd8-7770-a171-d7591adfd6db
created: 2026-06-05
---

# AI 小说转剧本 MVP 第一阶段契约设计

## 1. 本阶段目标

第一阶段不是写完整产品，而是锁定三类契约：

```text
实体模型契约
  -> API 契约
  -> YAML / JSON Schema 契约
```

这三类契约一旦稳定，成员 A 可以用 fixture 先做前端工作台，成员 B 可以用同一套结构实现 Python 后端、Pydantic 模型、AI skill wrapper 和校验服务。

第一阶段完成标准：

- 有稳定 ID 规则。
- 有最小实体模型。
- 有 API 路由草案。
- 有 screenplay YAML 顶层结构。
- 有每个 skill 的输入输出边界。
- 有三份 fixture 的字段口径：
  - `demo_novel_3_chapters.json`
  - `demo_story_bible.json`
  - `demo_screenplay.yaml`

## 2. 来自旧会话 workflow 的取舍

旧会话中对 `Supreme-Ultimate/novel-to-script-team` 的判断是：

- 它可以复用“编剧团队 workflow”和审核思想。
- 它的输出主要是 Markdown，不是产品级结构化协议。
- 它有 `novel-analyzer`、`script-writer`、`continuity-recorder`、`show-don’t-tell` 等可借鉴分工。
- 它缺少 `source_refs`、角色知识状态、scene-level YAML、Schema 校验和可编辑工作台数据层。

因此本项目采用“借鉴 workflow，不照搬产物”的方式：

| 参考 workflow | 本项目映射 | 产物 |
| --- | --- | --- |
| novel-analyzer | `NovelReaderSkill` | `novel_analysis` artifact |
| continuity-recorder | `StoryOntologySkill` + `ContinuityAuditorSkill` | `story_bible` + `audit_report` |
| adaptation-analysis / episode-planning | `AdaptationPlannerSkill` | `adaptation_plan` + `scene_plan` |
| script-writing | `ScreenplayYamlWriterSkill` | `screenplay_json` + `screenplay_yaml` |
| show-don’t-tell | `DialogueDoctorSkill` | dialogue subtext/action_hint |
| review-gates | `ValidationService` + `ContinuityAuditorSkill` | schema warnings + continuity warnings |

## 3. Premise Challenge

在锁契约前，先明确几个必须接受的前提：

1. **内部真相源应该是 JSON/Pydantic，不是 YAML 字符串。**  
   YAML 是最终导出格式；内部用 JSON/Pydantic 才能稳定校验、编辑和引用。

2. **第一阶段必须契约先行，而不是 prompt 先行。**  
   如果先写 prompt，模型会带着字段漂移；如果先定模型，prompt 只是把内容填进结构。

3. **Skill 负责创作判断，代码负责结构可信。**  
   人物动机、伏笔判断、潜台词属于 skill；ID 是否存在、字段是否缺失、引用是否断裂属于后端校验。

4. **前端第一版必须能脱离真实 AI 跑通。**  
   否则前端会被模型不稳定拖死。fixture 是并行开发的核心。

5. **本阶段只锁 MVP 够用字段，不追求全量剧本工业标准。**  
   不做 Final Draft、Fountain、预算、图数据库、协作版本 diff。

## 4. 备选路线与推荐

### 方案 A：YAML-first

让模型直接输出 YAML，前端直接展示，后端只做轻校验。

优点：

- 开发最快。
- demo 初看容易出结果。

缺点：

- 字段漂移严重。
- 引用校验困难。
- 用户编辑后难以回写结构。
- 后续 story_bible、audit、dialogue rewrite 很难稳定复用。

### 方案 B：Schema-first JSON internal，YAML export

模型输出 JSON，后端 Pydantic 校验，通过后导出 YAML。

优点：

- 最适合 Python 后端。
- 引用校验清楚。
- 前后端都能基于类型契约并行。
- YAML 仍满足比赛/演示要求。

缺点：

- 初期要多写一层转换和模型。

### 方案 C：Workflow-first

先把旧仓库的 Markdown workflow 跑顺，再逐步结构化。

优点：

- 创作方法论起步快。
- prompt 思路较成熟。

缺点：

- 产品内核会被 Markdown 流水线绑住。
- 后续要补 Schema 时容易返工。

推荐：**方案 B**。  
原因：本项目的真正亮点是“结构化、可追溯、可审查”，不是一次性生成文本。

## 5. ID 规则

所有跨实体引用必须使用稳定 ID。

| 实体 | ID 格式 | 示例 |
| --- | --- | --- |
| Project | `proj_<shortid>` | `proj_demo_001` |
| Chapter | `chapter_###` | `chapter_001` |
| Paragraph | `p_###` | `p_001` |
| Character | `char_###` | `char_001` |
| Relationship | `rel_###` | `rel_001` |
| Secret | `secret_###` | `secret_001` |
| Knowledge item | `know_###` | `know_001` |
| Event | `event_###` | `event_001` |
| Causal edge | `cause_###` | `cause_001` |
| Foreshadowing | `foreshadow_###` | `foreshadow_001` |
| Scene plan | `scene_plan_###` | `scene_plan_001` |
| Scene | `scene_###` | `scene_001` |
| Dialogue line | `line_###` | `line_001` |
| Warning | `warn_###` | `warn_001` |

规则：

- 章节、段落由代码生成，不交给模型。
- 角色、事件、伏笔可由模型建议，但后端负责去重和稳定化。
- 场景 ID 由后端根据 scene_plan 顺序生成。
- warning 必须引用具体实体 ID。

## 6. 实体模型草案

### 6.1 Project

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `id` | string | 是 | 项目 ID |
| `title` | string | 是 | 项目标题 |
| `logline` | string | 否 | 一句话简介 |
| `status` | enum | 是 | `draft` / `generating` / `ready` / `failed` |
| `created_at` | datetime | 是 | 创建时间 |
| `updated_at` | datetime | 是 | 更新时间 |

### 6.2 Chapter

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `id` | string | 是 | `chapter_001` |
| `title` | string | 是 | 章节标题 |
| `order` | integer | 是 | 排序 |
| `text` | string | 是 | 原文 |
| `paragraphs` | Paragraph[] | 是 | 分段结果 |
| `word_count` | integer | 是 | 字数 |

### 6.3 Paragraph

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `id` | string | 是 | `p_001` |
| `index` | integer | 是 | 章内序号 |
| `text` | string | 是 | 段落文本 |

### 6.4 SourceRef

`SourceRef` 是本项目最重要的可信字段之一。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `chapter_id` | string | 是 | 来源章节 |
| `paragraph_range` | string | 是 | 例如 `1-3` |
| `quote` | string | 否 | 可选原文摘录 |

### 6.5 Character

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `id` | string | 是 | 角色 ID |
| `name` | string | 是 | 角色名 |
| `aliases` | string[] | 否 | 别名 |
| `narrative_role` | enum | 否 | `protagonist` / `antagonist` / `supporting` |
| `goals.explicit` | string | 否 | 显性目标 |
| `goals.hidden` | string | 否 | 隐藏目标 |
| `secrets` | Secret[] | 否 | 秘密 |
| `voice_profile` | VoiceProfile | 否 | 角色声口 |
| `evidence_level` | enum | 是 | `explicit` / `inferred` / `ambiguous` |
| `source_refs` | SourceRef[] | 是 | 原文依据 |

### 6.6 VoiceProfile

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `rhythm` | string | 否 | 句式节奏 |
| `diction` | string | 否 | 用词习惯 |
| `avoidance_pattern` | string | 否 | 回避方式 |
| `emotional_leak` | string | 否 | 情绪泄露方式 |
| `sample_lines` | string[] | 否 | 原文或生成样例 |

### 6.7 RelationshipEdge

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `id` | string | 是 | 关系 ID |
| `from_character_id` | string | 是 | 起点角色 |
| `to_character_id` | string | 是 | 终点角色 |
| `type` | string | 是 | 关系类型 |
| `current_state` | string | 是 | 当前关系状态 |
| `evidence_level` | enum | 是 | `explicit` / `inferred` / `ambiguous` |
| `source_refs` | SourceRef[] | 是 | 原文依据 |

### 6.8 KnowledgeState

用于避免角色知道不该知道的信息。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `character_id` | string | 是 | 角色 ID |
| `knows` | string[] | 否 | 已知 event/secret/knowledge ID |
| `does_not_know` | string[] | 否 | 未知 event/secret/knowledge ID |
| `as_of_event_id` | string | 否 | 截止事件 |

### 6.9 Event

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `id` | string | 是 | 事件 ID |
| `title` | string | 是 | 事件标题 |
| `summary` | string | 是 | 事件摘要 |
| `event_type` | enum | 否 | `discovery` / `conflict` / `reveal` / `decision` / `turning_point` |
| `participants` | string[] | 是 | 角色 ID 列表 |
| `chapter_refs` | SourceRef[] | 是 | 原文来源 |
| `evidence_level` | enum | 是 | 证据等级 |

### 6.10 CausalEdge

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `id` | string | 是 | 因果边 ID |
| `from_event_id` | string | 是 | 原因事件 |
| `to_event_id` | string | 是 | 结果事件 |
| `relation` | enum | 是 | `causes` / `motivates` / `reveals` / `blocks` |
| `explanation` | string | 是 | 为什么是因果，不只是时间先后 |

### 6.11 Foreshadowing

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `id` | string | 是 | 伏笔 ID |
| `description` | string | 是 | 伏笔描述 |
| `setup_event_id` | string | 否 | 埋设事件 |
| `setup_scene_id` | string | 否 | 埋设场景 |
| `payoff_event_id` | string | 否 | 兑现事件 |
| `payoff_scene_id` | string | 否 | 兑现场景 |
| `status` | enum | 是 | `candidate` / `planned` / `paid_off` / `unresolved` |
| `source_refs` | SourceRef[] | 是 | 来源 |

### 6.12 AdaptationConfig

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `target_format` | enum | 是 | `short_drama` / `web_series` / `film` / `general` |
| `fidelity_level` | enum | 是 | `low` / `medium` / `high` |
| `preserve_priorities` | string[] | 是 | 保留重点 |
| `dialogue_style` | enum | 否 | `restrained` / `sharp` / `naturalistic` / `genre` |

### 6.13 AdaptationPlan

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `retained_events` | string[] | 是 | 保留事件 ID |
| `merged_events` | object[] | 否 | 合并事件及原因 |
| `deleted_or_deferred_events` | object[] | 否 | 删除/延后事件及原因 |
| `protected_elements` | string[] | 是 | 受保护关系/伏笔/事件 ID |
| `scene_plan` | ScenePlan[] | 是 | 场景计划 |

### 6.14 Scene

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `id` | string | 是 | 场景 ID |
| `title` | string | 是 | 场景标题 |
| `source_refs` | SourceRef[] | 是 | 来源 |
| `dramatic_purpose` | string[] | 是 | 戏剧目的 |
| `location` | Location | 是 | 场景地点 |
| `characters` | string[] | 是 | 角色 ID |
| `related_events` | string[] | 是 | 关联事件 |
| `causal_links.causes` | string[] | 否 | 原因事件 |
| `causal_links.effects` | string[] | 否 | 结果事件 |
| `foreshadowing.setups` | string[] | 否 | 埋设伏笔 |
| `foreshadowing.payoffs` | string[] | 否 | 兑现伏笔 |
| `action` | string[] | 是 | 动作描述 |
| `dialogue` | DialogueLine[] | 是 | 对白 |

### 6.15 DialogueLine

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `id` | string | 是 | 台词 ID |
| `character_id` | string | 是 | 角色 ID |
| `line` | string | 是 | 台词 |
| `surface_intent` | string | 是 | 表层意图 |
| `subtext` | string | 是 | 潜台词 |
| `emotional_state` | string | 否 | 情绪状态 |
| `action_hint` | string | 是 | 可表演动作 |

### 6.16 AuditWarning

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `id` | string | 是 | warning ID |
| `severity` | enum | 是 | `info` / `warning` / `error` |
| `type` | enum | 是 | `schema` / `source_ref` / `foreshadowing` / `knowledge_state` / `dialogue` |
| `message` | string | 是 | 展示文案 |
| `target` | object | 是 | 指向 scene/dialogue/event/character |
| `suggestion` | string | 否 | 修复建议 |
| `needs_human_review` | boolean | 是 | 是否需要人工确认 |

## 7. Artifact 契约

每一步 AI 结果都保存为 artifact。

| artifact type | 来源 skill/service | 内容 |
| --- | --- | --- |
| `novel_analysis` | `NovelReaderSkill` | characters candidates、events、locations、objects、foreshadowing_candidates |
| `story_bible` | `StoryOntologySkill` | characters、relationship_edges、knowledge_states |
| `adaptation_plan` | `AdaptationPlannerSkill` | retained/merged/protected/scene_plan |
| `screenplay_json` | `ScreenplayYamlWriterSkill` | scenes、dialogue、source_refs |
| `screenplay_yaml` | `YamlService` | 最终 YAML 字符串 |
| `audit_report` | `ContinuityAuditorSkill` + `ValidationService` | warnings |

Artifact 通用字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | string | artifact ID |
| `project_id` | string | 所属项目 |
| `type` | enum | artifact 类型 |
| `version` | integer | 版本号 |
| `data` | object/string | 结构化数据或 YAML |
| `created_at` | datetime | 创建时间 |
| `source_job_id` | string | 来源 job |

## 8. Skill 输入输出边界

### 8.1 NovelReaderSkill

输入：

```json
{
  "chapters": [
    {
      "id": "chapter_001",
      "title": "第一章 雨夜",
      "order": 1,
      "paragraphs": [
        { "id": "p_001", "index": 1, "text": "..." }
      ]
    }
  ]
}
```

输出：

```json
{
  "character_candidates": [],
  "events": [],
  "locations": [],
  "objects": [],
  "foreshadowing_candidates": []
}
```

约束：

- 不生成剧本。
- 不创建章节 ID。
- 推断内容必须标 `evidence_level`。
- 每个 event 必须带 `chapter_refs`。

### 8.2 StoryOntologySkill

输入：

```json
{
  "novel_analysis": {},
  "source_excerpt_policy": "quote_short_refs_only"
}
```

输出：

```json
{
  "story_bible": {
    "characters": [],
    "relationship_edges": [],
    "knowledge_states": []
  }
}
```

约束：

- 不把推断写成事实。
- 角色 ID 稳定。
- 关系必须有 evidence level。
- voice profile 必须来自原文样本或标为 inferred。

### 8.3 AdaptationPlannerSkill

输入：

```json
{
  "story_bible": {},
  "events": [],
  "causal_graph": { "edges": [] },
  "foreshadowing": [],
  "adaptation_config": {}
}
```

输出：

```json
{
  "adaptation_plan": {
    "retained_events": [],
    "merged_events": [],
    "deleted_or_deferred_events": [],
    "protected_elements": [],
    "scene_plan": []
  }
}
```

约束：

- 高忠实度下不得删除核心关系和关键伏笔。
- 合并/删除必须给 reason。
- 不直接写最终对白。

### 8.4 ScreenplayYamlWriterSkill

输入：

```json
{
  "story_bible": {},
  "adaptation_config": {},
  "adaptation_plan": {},
  "schema_summary": {}
}
```

输出：

```json
{
  "screenplay": {
    "schema_version": "1.0",
    "project": {},
    "source": {},
    "adaptation_config": {},
    "story_bible": {},
    "events": [],
    "causal_graph": { "edges": [] },
    "foreshadowing": [],
    "scenes": [],
    "audit_report": {}
  }
}
```

约束：

- 输出 JSON，不直接输出 YAML。
- scene 必须有 source_refs。
- dialogue.character_id 必须来自 story_bible。
- 每场必须有 dramatic_purpose、action、dialogue。

### 8.5 ContinuityAuditorSkill

输入：

```json
{
  "story_bible": {},
  "events": [],
  "foreshadowing": [],
  "scenes": []
}
```

输出：

```json
{
  "audit_report": {
    "continuity_warnings": [],
    "unresolved_foreshadowing": [],
    "dialogue_warnings": [],
    "schema_warnings": []
  }
}
```

约束：

- 只审查，不大规模重写。
- 每条 warning 必须指向具体 ID。
- 不确定问题标 `needs_human_review: true`。

### 8.6 DialogueDoctorSkill

输入：

```json
{
  "scene": {},
  "voice_profiles": [],
  "rewrite_direction": "restrained"
}
```

输出：

```json
{
  "dialogue": []
}
```

约束：

- 不把潜台词直接说出口。
- action_hint 必须可表演、可看见。
- 重写不破坏 scene 的因果和伏笔引用。

## 9. API 草案

### 9.1 Project API

| Method | Path | 用途 |
| --- | --- | --- |
| `POST` | `/api/projects` | 创建项目 |
| `GET` | `/api/projects/{project_id}` | 获取项目 |
| `PATCH` | `/api/projects/{project_id}` | 更新标题/logline |

创建项目请求：

```json
{
  "title": "雨夜旧案",
  "logline": "一个年轻女人在旧案中发现母亲死亡真相。"
}
```

### 9.2 Chapter API

| Method | Path | 用途 |
| --- | --- | --- |
| `PUT` | `/api/projects/{project_id}/chapters` | 覆盖保存章节列表 |
| `POST` | `/api/projects/{project_id}/chapters/auto-split` | 自动拆章 |
| `GET` | `/api/projects/{project_id}/chapters` | 获取章节 |

保存章节请求：

```json
{
  "chapters": [
    {
      "title": "第一章 雨夜",
      "order": 1,
      "text": "..."
    }
  ]
}
```

后端响应必须补全：

```json
{
  "chapters": [
    {
      "id": "chapter_001",
      "title": "第一章 雨夜",
      "order": 1,
      "word_count": 1200,
      "paragraphs": [
        { "id": "p_001", "index": 1, "text": "..." }
      ]
    }
  ],
  "validation": {
    "chapter_count": 3,
    "can_generate": true
  }
}
```

### 9.3 Generation API

| Method | Path | 用途 |
| --- | --- | --- |
| `POST` | `/api/projects/{project_id}/generate/story-bible` | 生成原著解析 + 故事圣经 |
| `POST` | `/api/projects/{project_id}/generate/adaptation-plan` | 生成改编计划 |
| `POST` | `/api/projects/{project_id}/generate/screenplay` | 生成剧本 JSON + YAML |
| `POST` | `/api/projects/{project_id}/generate/audit` | 生成审查报告 |
| `GET` | `/api/jobs/{job_id}` | 查询任务状态 |

统一任务响应：

```json
{
  "job_id": "job_001",
  "status": "queued",
  "current_step": "story_bible",
  "project_id": "proj_demo_001"
}
```

任务状态：

```json
{
  "job_id": "job_001",
  "status": "running",
  "current_step": "StoryOntologySkill",
  "progress": 60,
  "error": null,
  "artifact_ids": ["artifact_001"]
}
```

### 9.4 Artifact API

| Method | Path | 用途 |
| --- | --- | --- |
| `GET` | `/api/projects/{project_id}/artifacts` | 获取 artifact 列表 |
| `GET` | `/api/projects/{project_id}/artifacts/{type}` | 获取某类最新 artifact |
| `GET` | `/api/projects/{project_id}/artifacts/{type}/versions` | 获取版本 |

### 9.5 YAML / Schema API

| Method | Path | 用途 |
| --- | --- | --- |
| `POST` | `/api/projects/{project_id}/yaml/validate` | 校验用户编辑后的 YAML |
| `GET` | `/api/projects/{project_id}/yaml/download` | 下载 YAML |
| `GET` | `/api/projects/{project_id}/schema/download` | 下载 Schema 文档 |

YAML 校验请求：

```json
{
  "yaml": "schema_version: \"1.0\"\nproject:\n  title: \"雨夜旧案\""
}
```

YAML 校验响应：

```json
{
  "valid": false,
  "warnings": [
    {
      "id": "warn_001",
      "severity": "error",
      "type": "schema",
      "message": "scene_001 引用了不存在的角色 char_999",
      "target": {
        "scene_id": "scene_001",
        "character_id": "char_999"
      },
      "needs_human_review": false
    }
  ]
}
```

## 10. YAML Schema 草案

### 10.1 顶层结构

```yaml
schema_version: "1.0"

project:
  id: "proj_demo_001"
  title: "雨夜旧案"
  logline: ""
  target_format: "web_series"

source:
  chapters:
    - id: "chapter_001"
      title: "第一章 雨夜"
      order: 1
      paragraph_count: 12

adaptation_config:
  target_format: "web_series"
  fidelity_level: "high"
  preserve_priorities:
    - "relationship_arc"
    - "foreshadowing"
  dialogue_style: "restrained"

story_bible:
  characters: []
  relationship_edges: []
  knowledge_states: []

events: []

causal_graph:
  edges: []

foreshadowing: []

adaptation_plan:
  retained_events: []
  merged_events: []
  deleted_or_deferred_events: []
  protected_elements: []

scenes: []

audit_report:
  continuity_warnings: []
  unresolved_foreshadowing: []
  dialogue_warnings: []
  schema_warnings: []
```

### 10.2 最小可展示 scene

```yaml
scenes:
  - id: "scene_001"
    title: "雨夜重逢"
    source_refs:
      - chapter_id: "chapter_001"
        paragraph_range: "1-3"
        quote: "林晚在雨夜回到旧巷。"
    dramatic_purpose:
      - "建立林晚与周砚的紧张关系"
      - "埋下旧照片伏笔"
    location:
      name: "旧巷口"
      time: "night"
      interior_exterior: "EXT"
    characters:
      - "char_001"
      - "char_002"
    related_events:
      - "event_001"
    causal_links:
      causes:
        - "event_001"
      effects:
        - "event_004"
    foreshadowing:
      setups:
        - "foreshadow_001"
      payoffs: []
    action:
      - "林晚停在巷口，看见周砚手里攥着一块旧怀表。"
    dialogue:
      - id: "line_001"
        character_id: "char_001"
        line: "你怎么会在这里？"
        surface_intent: "质问对方出现原因"
        subtext: "她不愿承认自己一直在等他"
        emotional_state: "guarded"
        action_hint: "她把伞柄攥得更紧"
```

## 11. 引用校验规则

第一阶段至少锁以下规则：

| 规则 | 错误级别 | 说明 |
| --- | --- | --- |
| `source_refs.chapter_id` 必须存在 | error | 没来源，剧本不可追溯 |
| `scene.characters[]` 必须存在于 `story_bible.characters` | error | 防止模型发明角色 ID |
| `dialogue.character_id` 必须存在于 scene characters | error | 防止角色未出场却说话 |
| `related_events[]` 必须存在于 `events` | warning/error | MVP 可先 warning |
| `causal_graph.edges.from/to` 必须存在于 `events` | error | 因果链不能断 |
| `foreshadowing.setup_event_id` 必须存在于 `events` | warning | candidate 可宽松 |
| `foreshadowing.payoff_scene_id` 如果非空，必须存在于 `scenes` | warning | 未兑现可进入 audit |
| 每个 scene 至少有一个 `dramatic_purpose` | warning | 保证不是流水账 |
| 每句 dialogue 必须有 `surface_intent` 和 `subtext` | warning | 支撑潜台词亮点 |

## 12. 三份 fixture 的最终口径

### 12.1 `demo_novel_3_chapters.json`

目的：模拟用户输入和章节管理。

最小字段：

```json
{
  "project": {
    "title": "雨夜旧案",
    "logline": ""
  },
  "chapters": [
    {
      "id": "chapter_001",
      "title": "第一章 雨夜",
      "order": 1,
      "text": "...",
      "paragraphs": [
        {
          "id": "p_001",
          "index": 1,
          "text": "..."
        }
      ]
    }
  ]
}
```

### 12.2 `demo_story_bible.json`

目的：模拟 `NovelReaderSkill + StoryOntologySkill` 输出。

最小字段：

```json
{
  "story_bible": {
    "characters": [],
    "relationship_edges": [],
    "knowledge_states": []
  },
  "events": [],
  "causal_graph": {
    "edges": []
  },
  "foreshadowing": []
}
```

### 12.3 `demo_screenplay.yaml`

目的：模拟最终导出和前端剧本预览。

最小字段：

```yaml
schema_version: "1.0"
project: {}
source: {}
adaptation_config: {}
story_bible: {}
events: []
causal_graph:
  edges: []
foreshadowing: []
adaptation_plan: {}
scenes: []
audit_report: {}
```

## 13. 第一阶段实际任务清单

### 成员 A：产品 + 前端 + 调研

1. 写出 `demo_novel_3_chapters.json` 的真实 3 章短样例。
2. 用本文件字段做 `demo_story_bible.json` mock。
3. 用本文件字段做 `demo_screenplay.yaml` mock。
4. 根据 API 草案搭前端类型和 mock client。
5. 画出工作台低保真结构：导入、故事圣经、改编策略、剧本 YAML、审查。
6. 写 Schema 说明文档第一版，重点解释为什么 Schema 服务“可追溯改编”。

### 成员 B：后端 + 产品讨论

1. 把实体模型落成 Pydantic 草案。
2. 把 API 草案落成 FastAPI router skeleton。
3. 写 `ValidationService` 的引用校验规则。
4. 写 fake provider，让 generation job 不依赖真实模型也能跑。
5. 按 fixture 写每个 skill wrapper 的输入输出模型。
6. 实现 JSON -> YAML export 的最小版。

## 14. 本阶段完成后的下一步

完成第一阶段后，不急着优化 prompt。下一步应该先做这条端到端空跑：

```text
创建项目
  -> 保存 3 章
  -> fake 生成 story_bible
  -> fake 生成 adaptation_plan
  -> fake 生成 screenplay_json
  -> 导出 demo_screenplay.yaml
  -> 运行引用校验
```

只要这条链路跑通，真实 AI 的接入就是替换 provider 和 prompt，而不是重构产品。

## 15. The Assignment

下一步的具体行动：

```text
用 90 分钟共同锁定三份 fixture：
1. demo_novel_3_chapters.json
2. demo_story_bible.json
3. demo_screenplay.yaml

锁定标准：
- 所有 ID 能互相引用。
- 至少 2 个角色、3 个事件、1 条关系、1 个伏笔。
- 至少 2 场 scene。
- 至少 1 条 dialogue 带 surface_intent/subtext/action_hint。
- 至少 1 条 audit warning 能定位到 scene 或 foreshadowing。
```

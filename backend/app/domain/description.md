# Domain 领域模型层

`backend/app/domain/` 是整个后端的**核心业务模型**，全部用 Pydantic `BaseModel` 定义，不依赖数据库和 HTTP —— 是纯 Python 业务对象。共 10 个文件，围绕"**小说 → 剧本改编**"这个业务域建模。

---

## 模型层次关系

```
Source（源素材） → StoryBible（故事拆解） → AdaptationPlan（改编策略） → Screenplay（最终剧本）
                                                                         ↓
                                                                    AuditReport（校验）
```

---

## 逐文件拆解

### `common.py` — 跨域共享的小类型

- `SourceRef`：引用溯源（章节 + 段落范围）
- `Location`：场景地点 + 内/外景（INT/EXT）+ 日/夜/晨/昏（day/night/morning/dusk）
- `VoiceProfile`：角色语态特征
- `ValidationFinding`：通用校验发现
- `IdList`：ID 列表包装

### `project.py` — 项目主体

```python
Project(id, title, logline, target_format, metadata)
```

最顶层实体，一个项目 = 一部要改编的作品。

### `source.py` — 源素材（小说原文）

```
Chapter → [Paragraph]
```

- `Chapter`：持有 `source_file`（原文章节文件）、`source_anchor`（定位锚点）
- `Paragraph`：持有 `text` + `summary`
- `ChapterSet`：章节集合

### `story_bible.py` — 故事圣经（叙事要素提取）

LLM 做叙事分析后的结构化输出，是整个领域模型中体量最大的模块：

| 模型 | 内容 |
|---|---|
| `Character` | 角色名、别名、叙事角色、目标、语态、出处引用 |
| `RelationshipEdge` | 角色间关系（类型、当前状态、证据等级） |
| `KnowledgeState` | 角色知情状态（知道什么 / 不知道什么） |
| `StoryBible` | 汇总上述三者 |
| `Event` | 叙事事件（类型、参与者、摘要） |
| `CausalEdge` / `CausalGraph` | 事件的因果链条 |
| `Foreshadowing` | 伏笔（setup → payoff，含状态追踪） |

### `adaptation.py` — 改编配置与计划

- `AdaptationConfig`：改编参数（忠实度 low/medium/high、对话风格、保留优先级等）
- `AdaptationPlan`：具体操作 — 保留/合并/删除/推迟哪些事件，以及场景规划
- 辅助模型：`MergedEvent`、`DeferredEvent`、`ScenePlanItem`

### `screenplay.py` — 剧本（最终产物，聚合根）

```
Screenplay
├── project: ScreenplayProject      ← 项目摘要
├── source: SourceBlock             ← 源素材摘要
├── adaptation_config               ← 改编配置
├── script_structure                ← 故事梗概/大纲/文学剧本格式声明
├── story_bible: StoryBible         ← 角色/关系/知情状态
├── core_elements                   ← 动作/情节/情境/主题/主人公/人物关系索引
├── events: [Event]                 ← 叙事事件列表
├── causal_graph: CausalGraph       ← 因果图
├── foreshadowing: [Foreshadowing]  ← 伏笔追踪
├── adaptation_plan                 ← 改编操作计划
├── scenes: [Scene]                 ← 最终剧本场景
│   ├── scene_heading               ← 单独成行的场景标题
│   ├── location, characters, dramatic_purpose
│   ├── action: [str]               ← 动作描写
│   ├── content_blocks              ← 标题下方自然段正文
│   └── dialogue: [DialogueLine]    ← 对白（含潜台词、情感状态）
└── audit_report: AuditReport       ← 内嵌校验报告
```

`ScriptStructure` 固定“故事梗概 -> 故事大纲 -> 文学剧本”的训练链路。  
`CoreElements` 是索引层，不替代 `story_bible` 或 `scenes`，只把动作、情节、情境、主题、主人公和人物关系集中成可校验引用。  
`SceneHeading` 对应文学剧本中单独成行的场景标题，必须能由前端直接显示。

### `audit.py` — 校验与审计

```python
AuditWarning(id, severity, target, message, needs_human_review)
AuditReport(continuity_warnings, unresolved_foreshadowing, dialogue_warnings, schema_warnings)
```

按类别分桶的校验警告，`needs_human_review` 标记哪些需要人工介入。

### `artifacts.py` — 产物元数据

`Artifact` 对应数据库的 `artifacts` 表，记录每一步产物的类型和版本。支持 6 种类型，对应完整工作流流水线：

```
novel_analysis → story_bible → adaptation_plan → screenplay_json → screenplay_yaml → audit_report
```

### `jobs.py` — 异步任务

`GenerationJob` 对应数据库的 `generation_jobs` 表，状态机：`queued → running → succeeded/failed`。

### `llm_runs.py` — LLM 调用记录

`LlmRun` 记录每次 LLM 调用的 provider、model、prompt_version、原始输出、解析结果、校验错误，提供完整的调用链可追溯性。

---

## 设计原则

- **纯 Pydantic 模型**：不 import FastAPI、SQLite 或任何基础设施依赖
- **单一真相源**：所有层（API、DB、Service）都引用这里的模型定义
- **聚合根模式**：`Screenplay` 作为顶层聚合根，内嵌所有子模型，一个对象完整描述改编全流程

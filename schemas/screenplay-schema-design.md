# Screenplay Schema 设计说明

## 设计目标

本 schema 描述的是“可审查的结构化改编资产”，不是一段普通剧本文本。它把原文引用、故事圣经、改编决策、文学剧本格式、场景正文和审计警告放在同一个可校验结构里，让后端能在导出前确认字段完整、引用不断链。

## Canonical Source

`schemas/screenplay.schema.json` 是机器可读的 canonical schema。  
`schemas/screenplay.schema.yaml` 是给人阅读和文档联调用的摘要，不替代 JSON Schema。

## 文学剧本格式要求

schema version `1.1` 明确吸收文学剧本格式要点：

- 基本单位是 `scene`，顶层 `scenes` 是最终剧本正文的唯一场景列表。
- 每个 scene 必须有 `scene_heading`，用于表示单独成行的场景标题。
- `scene_heading` 必须包含 `sequence`、`location`、`interior_exterior`、`time_of_day` 和可直接显示的 `text`。
- `interior_exterior` 使用 `INT`、`EXT`、`INT/EXT`，方便和外部剧本工具联调。
- `time_of_day` 使用 `day`、`night`、`morning`、`dusk`，对应日、夜、晨、昏。
- `content_blocks` 表示场景标题下方的自然段内容，保留 `action` 和 `dialogue` 作为结构化编辑入口。

## 为什么新增 script_structure

文学剧本训练通常会经过“故事梗概 -> 故事大纲 -> 文学剧本”。如果 schema 只保存最终场景，系统很难解释这版剧本是怎么从宏观结构落到场次的。

`script_structure` 因此包含：

- `story_synopsis`：故事梗概。
- `story_outline`：故事大纲，使用 `outline_###` 并关联 `event_###` 与 `scene_###`。
- `literary_screenplay`：声明最终文学剧本以 `scene` 为基本单位，并列出场景 ID。

## 为什么新增 core_elements

用户给出的核心元素包括动作、情节、情境、主题、主人公、人物关系。原 schema 已经分别有 `events`、`story_bible.relationship_edges`、scene `action` 等字段，但这些字段分散在不同层级，评审和前端很难一眼看出“核心元素是否齐全”。

`core_elements` 作为一个索引层，把核心元素收拢起来：

- `actions` 指向具体 scene 和可选 event。
- `plot` 指向事件序列和情节功能。
- `situations` 指向具体 scene 中的情境压力。
- `theme` 保存主题表达。
- `protagonists` 引用主人公 `char_###`。
- `character_relationships` 引用人物关系 `rel_###`。

## 为什么仍保留 story_bible 和 adaptation_plan

`story_bible` 提供角色、关系、知情状态的稳定 ID，是后续台词、审计和引用校验的基础。  
`adaptation_plan` 记录哪些事件被保留、合并、删除或推迟，以及每场 scene 的来源事件，保证 screenplay 不是黑箱生成结果。

如果删除这两层，系统只能展示“生成了一份剧本”，不能回答“为什么这样改”和“哪些原文资产被保护”。

## JSON 与 YAML 的分工

后端内部使用 JSON/Pydantic 作为 truth source。  
YAML 是面向用户、评审和 demo 的导出格式。用户编辑 YAML 后，必须先解析回 JSON，再走 schema validation 和 reference validation。

## Schema 不负责的事

JSON Schema 只检查字段形状、必填项、枚举和 ID 字符串格式。它不证明：

- `char_001` 是否真的存在于 `story_bible.characters`。
- `scene_heading.location` 是否和 `location.name` 语义一致。
- `core_elements.protagonists` 是否引用了存在的角色。
- `dialogue.character_id` 是否属于当前 scene 的 `characters`。

这些跨实体检查属于 `backend/app/validators/reference_validator.py`。

## Future Compatibility

V0+V1 只把文学剧本所需的核心字段固定下来。后续版本应该扩展字段，而不是替换主结构：

- V2 可增强 `story_bible`。
- V3 可增强 `causal_graph` 和 `foreshadowing`。
- V4 可增强 `dialogue`、`content_blocks` 和潜台词改写。
- V5 可增强 `audit_report` 和人工复审闭环。

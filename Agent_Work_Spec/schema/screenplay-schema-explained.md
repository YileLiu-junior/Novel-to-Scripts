# Screenplay Schema 说明

screenplay schema 定义了一份结构化的文学剧本改编文件。它同时回答四个问题：

1. 每场戏的源素材来自哪里？
2. 每场戏是否符合文学剧本的 scene 格式？
3. 这场戏依赖哪些故事实体、核心元素和改编决策？
4. 在采信输出结果之前，哪些 warning 需要人工复核？

## 顶层结构

- `project`：项目标题、logline、目标格式。
- `source`：章节 ID 列表和源文件指针。
- `adaptation_config`：用户控制的改编参数。
- `script_structure`：故事梗概、故事大纲、文学剧本格式声明。
- `story_bible`：角色、人物关系、知情状态。
- `core_elements`：动作、情节、情境、主题、主人公、人物关系的索引。
- `events`：已确定的故事事件。
- `causal_graph`：事件之间的因果链接。
- `foreshadowing`：伏笔的铺设与回收引用。
- `adaptation_plan`：保留、合并、推迟及受保护的故事资产。
- `scenes`：文学剧本的 scene 列表，也是最终正文主体。
- `audit_report`：由校验器或审计 skill 生成的 warning。

## 文学剧本格式

每个 `scene` 必须包含 `scene_heading`：

- `sequence`：场次序号。
- `location`：地点。
- `interior_exterior`：`INT`、`EXT` 或 `INT/EXT`，对应内景、外景、内外景。
- `time_of_day`：`day`、`night`、`morning`、`dusk`，对应日、夜、晨、昏。
- `text`：可直接单独成行展示的场景标题。

每个 `scene` 还必须包含 `content_blocks`。它表示场景标题下方的自然段正文，`block_type` 可区分 `action`、`dialogue` 或 `transition`。为了便于前端编辑和后续台词打磨，schema 仍保留 `action` 和 `dialogue` 两个结构化字段。

## 结构训练与核心元素

`script_structure` 保存“故事梗概 -> 故事大纲 -> 文学剧本”的训练链路：

- `story_synopsis` 是故事梗概。
- `story_outline` 是大纲条目，关联 `event_###` 和 `scene_###`。
- `literary_screenplay.unit` 固定为 `scene`。

`core_elements` 把文学剧本核心元素收拢到一个可检查位置：

- `actions`：动作。
- `plot`：情节。
- `situations`：情境。
- `theme`：主题。
- `protagonists`：主人公，引用 `char_###`。
- `character_relationships`：人物关系，引用 `rel_###`。

## 校验分工

Schema validation 检查形状，reference validation 检查含义。

示例：

- Schema 可以要求 `scene.scene_heading.time_of_day` 必须是 `day/night/morning/dusk` 之一。
- Reference validation 检查 `core_elements.protagonists` 中的角色 ID 是否在 `story_bible.characters` 中存在。
- Schema 可以要求 `dialogue.character_id` 字段存在。
- Reference validation 检查对白说话人是否属于当前 scene 的 `characters`。

## Demo 用例

使用以下文件：

- `fixtures/demo_screenplay.json`
- `fixtures/demo_screenplay.yaml`
- `fixtures/demo_invalid_refs.yaml`

其中 `demo_invalid_refs.yaml` 保持 schema 形状完整，但故意包含不存在的 ID 引用，用于证明校验器能够捕获断裂的引用关系。

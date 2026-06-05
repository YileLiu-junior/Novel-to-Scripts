# Screenplay Schema 说明

screenplay schema 定义了一个结构化的改编文件。它回答三个问题：

1. 每场戏的源素材来自哪里？
2. 这场戏依赖了哪些故事实体？
3. 在采信输出结果之前，哪些警告需要人工复核？

## 顶层结构

- `project`：项目标题、logline、目标格式。
- `source`：章节 ID 列表和源文件指针。
- `adaptation_config`：用户控制的改编参数。
- `story_bible`：角色、关系、知情状态。
- `events`：已确定的故事事件。
- `causal_graph`：事件之间的因果链接。
- `foreshadowing`：伏笔的铺设与回收引用。
- `adaptation_plan`：保留、合并、推迟及受保护的故事资产。
- `scenes`：剧本场景、动作、对白、源素材引用。
- `audit_report`：由校验器或审计 skill 生成的警告。

## 校验分工

Schema 校验检查形状。引用校验检查含义。

示例：

- Schema 可以要求 `scene.characters` 必须是数组。
- 引用校验检查每个角色 ID 是否在 `story_bible` 中存在。
- Schema 可以要求 `dialogue.character_id` 字段必须存在。
- 引用校验检查对白说话人是否属于当前场景的角色列表。

## Demo 用例

使用以下文件：

- `fixtures/demo_screenplay.json`
- `fixtures/demo_screenplay.yaml`
- `fixtures/demo_invalid_refs.yaml`

其中 `demo_invalid_refs.yaml` 故意包含不存在的 ID 引用，用于证明校验器能够捕获断裂的引用关系。
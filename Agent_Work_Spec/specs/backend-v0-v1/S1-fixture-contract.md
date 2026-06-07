# S1 测试夹具合约

## 负责人

合约架构师（Contract Architect）。

## 目的

在 domain、API、prompt 或前端代码开始推进之前，锁定共享语言。测试夹具（fixtures）是后端、前端、测试和skills之间达成一致的第一个锚点。

## 文件

- `fixtures/demo_novel_3_chapters.json`
- `fixtures/demo_story_bible.json`
- `fixtures/demo_screenplay.json`
- `fixtures/demo_screenplay.yaml`
- `fixtures/demo_audit_report.json`
- `fixtures/demo_invalid_refs.yaml`

## 合约条款

- JSON/Pydantic 为内部唯一事实来源。
- YAML 作为导出格式和用户可编辑的交换格式。
- 测试夹具中的 ID 必须与最终后端 ID 格式一致：
  - `chapter_###`
  - `p_###`
  - `char_###`
  - `event_###`
  - `scene_###`
  - `line_###`
  - `warning_###`
- `demo_novel_3_chapters.json` 必须包含至少三章。
- 演示用故事圣经（story bible）必须包含至少两个角色、三个事件、一条关系、一条伏笔和知识状态示例。
- 演示用剧本必须包含至少两个场景及其来源引用。
- 无效引用测试夹具必须包含至少一条断裂的 `character_id` 或 `event_id`。

## 评审关卡

验收门槛 1（合约）仅在测试夹具的变更同步反映到 schema、domain 模型、DTO 和 prompt 参考示例中时，方可通过。


from app.validators.reference_validator import ReferenceValidator

__all__ = ["ReferenceValidator"]

# backend/app/validators/ — 校验规则层

#   这是剧本质量的守门员，4 个校验器各管一个维度，全部输出统一的 ValidationFinding 结构。

#   ---
#   4 个校验器

#   SchemaValidator — JSON Schema 结构校验

#   剧本 dict → jsonschema.Draft202012Validator → [ValidationFinding]

#   - 加载 schemas/screenplay.schema.json，用 JSON Schema 2020-12 规范逐字段校验
#   - 如果 jsonschema 包没装，降级为 warning 而非崩溃
#   - 错误带 path 字段（如 scenes.0.dialogue.2.line），精确定位到嵌套路径

#   ReferenceValidator — 引用完整性校验（跨实体 ID 一致性）

#   这是最复杂的一个校验器，检查整个剧本 JSON 里的 ID 引用是否悬空：

#   ┌─────────────────────────────────────┬─────────┬──────────────┐
#   │               检查项                │ 严重度  │     说明     │
#   ├─────────────────────────────────────┼─────────┼──────────────┤
#   │ 场景引用的 chapter_id 不存在        │ error   │ 溯源断链     │
#   ├─────────────────────────────────────┼─────────┼──────────────┤
#   │ 场景角色不在 character 列表中       │ error   │ 角色幽灵     │
#   ├─────────────────────────────────────┼─────────┼──────────────┤
#   │ 场景关联的事件不存在                │ warning │ 事件悬空     │
#   ├─────────────────────────────────────┼─────────┼──────────────┤
#   │ 对话角色不在场景角色列表中          │ error   │ 台词归属错误 │
#   ├─────────────────────────────────────┼─────────┼──────────────┤
#   │ 因果图边的 from/to 事件不存在       │ warning │ 因果断链     │
#   ├─────────────────────────────────────┼─────────┼──────────────┤
#   │ 伏笔的 setup 事件/payoff 场景不存在 │ warning │ 伏笔悬空     │
#   └─────────────────────────────────────┴─────────┴──────────────┘

#   先用集合推导把所有 chapters/characters/events/scenes 的 ID 聚拢，再逐条遍历检查，O(n) 搞定。

#   ChapterValidator — 前置条件校验

#   在生成前拦住不合规输入：
#   - 章节数 < 3 → error
#   - 任意章节文本为空 → error

#   AuditValidator — 校验发现 → 分桶报告

#   把 ValidationFinding 列表转换为 AuditReport：

#   findings ──┬── code 以 "schema." 开头  →  schema_warnings
#              └── 其他                      →  continuity_warnings

#   规则是：
#   - 生成 warning_id 分配结构化 ID
#   - severity != "info" 时自动标 needs_human_review=True
#   - 组装成 AuditWarning 放到对应的桶里

#   ---
#   在架构中的位置

#   ValidationService（组合层）
#       ├── SchemaValidator      ← 结构对错
#       ├── ReferenceValidator   ← 引用是否悬空
#       └── AuditValidator       ← 分桶 + 是否需要人工看
#               ↑
#               └── ChapterValidator  ← 独立的"能否开始生成"校验

#   设计要点：
#   - 所有校验器统一输出 ValidationFinding，上层可以混用、合并、分桶
#   - 每个校验器独立可测，Service 层按需组合
#   - ReferenceValidator 的 _finding() 私有工厂方法保证输出格式一致
"""Repository boundary for persistence."""

# 编排层——把领域模型、仓库、导出器、校验器、AI Skill 串成可执行的业务逻辑。路由只做 HTTP 分派，真正的活都在这里。
# 8 个服务，分三层角色

# 🧩 基础服务（薄封装）

#   ┌─────────────────┬────────────────┬────────────────────────────────────────────────────────────────┐
#   │      服务       │      依赖      │                              职责                              │
#   ├─────────────────┼────────────────┼────────────────────────────────────────────────────────────────┤
#   │ SchemaService   │ SchemaExporter │ 一行透传，把 JSON Schema 文件内容返回给调用方                  │
#   ├─────────────────┼────────────────┼────────────────────────────────────────────────────────────────┤
#   │ ArtifactService │ 无             │ 工厂方法，拼一个 Artifact 对象（artifact_{project}_{type}_v1） │
#   ├─────────────────┼────────────────┼────────────────────────────────────────────────────────────────┤
#   │ JobService      │ 无             │ GenerationJob 的创建 + 状态流转（model_copy 做不可变更新）     │
#   ├─────────────────┼────────────────┼────────────────────────────────────────────────────────────────┤
#   │ LlmTraceService │ 无             │ 记录 LLM 调用快照，当前用 fake provider 做桩                   │
#   └─────────────────┴────────────────┴────────────────────────────────────────────────────────────────┘

# 这层很薄，主要作用是把"怎么造对象"集中在一处，避免路由直接拼接。

#   ---
#   🔧 组合服务（串联多个组件）

#   ┌─────────────────┬─────────────────────────────────────────────────┬───────────────────────────────────────────────────────────────┐
#   │      服务       │                      依赖                       │                             职责                              │
#   ├─────────────────┼─────────────────────────────────────────────────┼───────────────────────────────────────────────────────────────┤
#   │                 │                                                 │ 把原始 [{"title":..., "text":...}] 字典列表规范化成 [Chapter] │
#   │ ChapterService  │ core/ids、ChapterValidator                      │  领域对象——自动分段、分配                                     │
#   │                 │                                                 │ ID、排序；并支持校验"是否可进入生成阶段"                      │
#   ├─────────────────┼─────────────────────────────────────────────────┼───────────────────────────────────────────────────────────────┤
#   │                 │                                                 │ 导出前校验 + 导入后校验。export_validated() 先跑              │
#   │ YamlService     │ YamlExporter、ValidationService                 │ schema/reference 校验，有 error 就拒绝导出；validate_yaml()   │
#   │                 │                                                 │ 解析 YAML 后跑同一套校验                                      │
#   ├─────────────────┼─────────────────────────────────────────────────┼───────────────────────────────────────────────────────────────┤
#   │ ValidationServi │ SchemaValidator、ReferenceValidator、AuditValid │ 组合三个校验器，对外只暴露两个入口：validate_screenplay()（sc │
#   │ ce              │ ator                                            │ hema + 引用完整性）和 audit_report_for()（findings →          │
#   │                 │                                                 │ 分桶的报告）                                                  │
#   └─────────────────┴─────────────────────────────────────────────────┴───────────────────────────────────────────────────────────────┘

#   这里体现了 Service 组合下层组件、对外暴露单一职责 API 的模式。

#   ---
#   🎯 核心编排器

#   GenerationOrchestrator — 整个改编流水线的指挥官

#   这是整个后端最核心的一个类。run_v1() 方法定义了一条 4 阶段 AI 工作流：

#   novel_reader          →  novel_analysis       (Artifact: novel_analysis)
#       ↓
#   story_ontology        →  story_assets         (Artifact: story_bible)
#       ↓
#   adaptation_planner    →  adaptation_plan      (Artifact: adaptation_plan)
#       ↓
#   screenplay_writer     →  screenplay_json      (Artifact: screenplay_json)
#       ↓                       ↓
#       └── validation_service  →  audit_report   (Artifact: audit_report)
#            └── yaml_service   →  yaml_text      (Artifact: screenplay_yaml)

#   每一步：
#   每一步：
#   1. JobService.mark_step() 更新任务状态和当前步骤
#   2. 调用对应的 AI Skill（来自 app/ai/skills/）
#   3. ArtifactService 保存中间产物
#   4. LlmTraceService 记录 LLM 调用快照

#   最后跑 ValidationService 做全量校验，生成 AuditReport 嵌入剧本，再通过 YamlService 转为 YAML。异常时 mark_step("failed", ..., str(exc)) 做优雅降级。

#   ---
#   依赖方向

#   生成编排器 (orchestrator)
#       ├── AI Skills (app/ai/skills/)      ← LLM 调用
#       ├── 基础服务 (artifact/job/trace)   ← 产物/任务/追踪
#       ├── 组合服务 (validation/yaml)      ← 校验/导出
#       │       └── Exporters               ← 格式转换
#       │       └── Validators              ← 校验规则
#       └── 领域模型 (domain/)              ← 数据结构定义

#   所有 Service 默认在构造函数里接收依赖实例，也提供默认值，兼顾了可测试性（测试时注入 mock）和开箱即用（生产环境不用手动装配）。
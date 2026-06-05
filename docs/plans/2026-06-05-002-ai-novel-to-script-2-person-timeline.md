---
title: AI 小说转剧本 MVP 双人并行时间顺序表
status: active
origin: docs/plans/2026-06-05-001-architecture-ai-novel-to-script-plan.md
created: 2026-06-05
---

# AI 小说转剧本 MVP 双人并行时间顺序表

## 1. 分工假设

团队 2 人：

- 成员 A：产品 + 前端 + 调研。负责流程定义、UI、样例数据、Schema 文档、demo 叙事、前端集成。
- 成员 B：产品前期调研讨论 + 后端实现。负责 FastAPI、数据模型、AI skill 封装、生成流水线、校验、导出。

并行策略：

- 先锁“数据契约”，再分头做 UI 和后端。
- 前端先用 fixture/mock 数据跑通体验。
- 后端先用 fake provider 跑通 pipeline，再替换真实模型调用。
- 每天至少有一个可集成版本，不把集成留到最后。

## 2. 模块依赖总览

| 模块 | 开发内容 | Skill 内容 | 前置依赖 | 后置影响 | 是否可并行 |
| --- | --- | --- | --- | --- | --- |
| M0 产品叙事与范围锁定 | 明确 demo 主线、功能取舍、命名、成功标准 | 无 | 原 MVP 方案 | 影响所有模块优先级 | 需要两人共同先做 |
| M1 数据契约与样例 | 顶层 JSON/YAML 结构、ID 规则、fixture、API 响应草案 | 每个 skill 的输入/输出字段草案 | M0 | 前端 mock、后端模型、prompt 都依赖它 | 共同完成后可全线并行 |
| M2 项目骨架 | React/Vite 工作台骨架；FastAPI 骨架 | 无 | M1 最小契约 | 后续 UI/API 集成 | 前后端可并行 |
| M3 多章节输入 | 章节 UI、字数、3 章校验；后端章节 API、段落编号 | NovelReaderSkill 消费结构化章节，不负责章节管理 | M1/M2 | source_refs、故事圣经、剧本来源 | 前后端可并行，接口需对齐 |
| M4 原著解析 | 后端保存 analysis artifact；前端展示解析进度和摘要 | NovelReaderSkill | M3 章节结构 | StoryOntologySkill、事件/伏笔 | Skill 可先用 prompt + fixture 并行写 |
| M5 故事圣经 | 人物卡、关系、秘密、知识状态 UI；后端 Pydantic 模型与 artifact | StoryOntologySkill | M4 输出 | 改编计划、台词声音、审查 | 前端可用 fixture 先做 |
| M6 可控改编 | 改编策略面板；后端 config 接收与保存 | AdaptationPlannerSkill | M5 story_bible + events | 剧本 scene_plan | 策略 UI 可提前做，skill 依赖 M5 字段 |
| M7 剧本生成与 YAML | 场景列表、详情、YAML 预览；后端 screenplay 模型、YAML 导出 | ScreenplayYamlWriterSkill | M5/M6 + Schema 摘要 | 审查、导出、demo 主输出 | 前端可用 demo_screenplay.yaml 先做 |
| M8 Schema/引用校验 | 校验 API、错误展示、下载 Schema 文档 | 可选 JsonRepair/YamlRepairSkill | M1/M7 | 审查可信度、导出可信度 | 后端优先，前端展示可并行 |
| M9 因果/伏笔审查 | 审查面板、warning 定位；后端 audit_report | ContinuityAuditorSkill | M5 events/foreshadowing + M7 scenes | demo 技术亮点 | 依赖生成剧本，但 UI 可提前用假数据 |
| M10 潜台词/角色声音 | 台词详情、voice profile 标签、关键场景重写入口 | DialogueDoctorSkill | M5 voice_profile + M7 scenes | demo 创作者亮点 | 最好后置，只做关键场景 |
| M11 Demo 与交付 | 示例小说、示例 YAML、演示脚本、README | prompt 版本冻结 | M7/M8，最好有 M9/M10 | 最终演示 | 两人共同收口 |

## 3. 强顺序约束

必须串行的链路：

```text
章节结构
  -> NovelReaderSkill
  -> StoryOntologySkill
  -> AdaptationPlannerSkill
  -> ScreenplayYamlWriterSkill
  -> ContinuityAuditorSkill
```

原因：

- `NovelReaderSkill` 需要稳定的 `chapter_id` 和段落编号。
- `StoryOntologySkill` 需要原著解析结果，不能凭空建故事圣经。
- `AdaptationPlannerSkill` 需要人物、事件、关系、伏笔，才能决定保留/合并/压缩。
- `ScreenplayYamlWriterSkill` 需要 scene_plan、story_bible 和 Schema 摘要。
- `ContinuityAuditorSkill` 需要最终 scenes 才能检查伏笔、知识状态和 source_refs。

可以并行的工作：

- 前端工作台布局可以和后端骨架并行。
- Schema 文档可以和后端模型并行写，但字段必须同步。
- Skill prompt 草案可以和后端封装并行写。
- 前端所有展示面板都可以先用 fixture 数据做。
- Demo 脚本、产品叙事、示例小说可以与开发并行推进。

## 4. 72h 双人并行时间表

### Day 0 / H0-H4：锁范围与数据契约

| 时间 | 成员 A：产品 + 前端 + 调研 | 成员 B：后端 + 产品讨论 | 交付物 | 依赖说明 |
| --- | --- | --- | --- | --- |
| H0-H1 | 共同确认 demo 主线：不是一键生成，而是可追溯改编工作台 | 共同确认技术主线：Python 后端保证结构可信 | MVP 范围冻结 | 所有后续任务的优先级依据 |
| H1-H2 | 定义页面信息架构、Tab、右侧面板内容 | 定义后端实体：Project、Chapter、Artifact、Job | 模块边界草案 | 先定边界，避免前后端互相等待 |
| H2-H4 | 写 fixture 草案：3 章小说、story_bible、screenplay、audit_report | 写 Pydantic/JSON Schema 草案和 API 响应草案 | `fixtures` + 数据契约 v0 | 这是并行开发的关键握手点 |

### Day 1 / H4-H24：骨架 + 故事圣经

| 时间 | 成员 A：产品 + 前端 + 调研 | 成员 B：后端 + 产品讨论 | 交付物 | 依赖说明 |
| --- | --- | --- | --- | --- |
| H4-H8 | 搭 React/Vite 工作台布局，完成导入页静态版 | 搭 FastAPI 项目，完成项目/章节 API 骨架 | 前后端可启动 | 依赖数据契约 v0 |
| H8-H12 | 实现章节输入、3 章校验、字数统计、生成按钮状态 | 实现章节分段、`chapter_001` ID、artifact 保存 | 多章节输入闭环 | M3 是所有 source_refs 的前置 |
| H12-H16 | 用 fixture 做故事圣经面板：人物卡、关系、事件、伏笔候选 | 封装 fake provider，写 NovelReaderSkill prompt 和解析结果模型 | 原著解析最小版 | 前端无需等真实 AI |
| H16-H20 | 打磨故事圣经 UI，并补充 demo 示例小说 | 写 StoryOntologySkill prompt，输出 story_bible artifact | 故事圣经最小版 | StoryOntology 依赖 NovelReader 输出 |
| H20-H24 | 前端接入真实/模拟 story-bible API，整理页面文案 | 联调 `/generate/story-bible` job 状态与 artifact 查询 | Day 1 集成版 | 当晚必须有“导入 -> 故事圣经”演示 |

### Day 2 / H24-H48：改编策略 + YAML 剧本

| 时间 | 成员 A：产品 + 前端 + 调研 | 成员 B：后端 + 产品讨论 | 交付物 | 依赖说明 |
| --- | --- | --- | --- | --- |
| H24-H28 | 实现改编策略面板：目标格式、忠实度、保留重点、台词风格 | 定义 `AdaptationConfig`、`AdaptationPlan` 模型 | 改编配置可保存 | UI 可早于 skill 完成 |
| H28-H32 | 写“AI 为什么这样改”的展示区，用 fixture 占位 | 写 AdaptationPlannerSkill，生成 retained/merged/protected/scene_plan | 改编计划最小版 | 依赖 story_bible + events |
| H32-H36 | 实现场景列表和场景详情静态版 | 写 ScreenplayYamlWriterSkill，生成 screenplay JSON | 剧本结构最小版 | 依赖 scene_plan + Schema 摘要 |
| H36-H40 | 实现 YAML 预览、复制、下载按钮 UI | 实现 JSON -> YAML 导出，基础 Schema 校验 | YAML 输出闭环 | 内部 JSON，外部 YAML |
| H40-H44 | 前端接入 screenplay API，展示 source_refs、events、foreshadowing | 实现引用校验：character/event/scene/foreshadowing | 可追溯剧本 | 这是技术可信度核心 |
| H44-H48 | 准备 Day 2 demo 路径，记录卡点 | 联调 `/generate/adaptation-plan`、`/generate/screenplay`、`/yaml/download` | Day 2 集成版 | 当晚必须能导出 YAML |

### Day 3 / H48-H72：审查亮点 + Demo 收口

| 时间 | 成员 A：产品 + 前端 + 调研 | 成员 B：后端 + 产品讨论 | 交付物 | 依赖说明 |
| --- | --- | --- | --- | --- |
| H48-H52 | 实现审查面板列表和 warning 定位交互 | 写 ContinuityAuditorSkill，先覆盖未兑现伏笔和缺失 source_refs | 审查最小版 | 依赖 scenes/events/foreshadowing |
| H52-H56 | 实现台词详情：surface intent、subtext、action hint | 写 DialogueDoctorSkill，只处理 1-2 场关键戏 | 潜台词高光版 | 依赖 voice_profile + scenes |
| H56-H60 | 写 Schema 说明文档：为什么字段服务改编逻辑 | 实现 `/schema/download`，补 schema_warnings | Schema 文档导出 | 比赛硬要求，不能后置到最后一小时 |
| H60-H64 | 统一 UI 文案、空状态、错误状态、演示路径 | 修生成失败、校验失败、job 状态异常 | 可演示候选版 | 进入 bug bash |
| H64-H68 | 准备最终 demo：示例小说、点击路径、讲稿 | 固化 prompt 版本、关闭不稳定实验项 | Demo 冻结版 | 不再横向扩功能 |
| H68-H72 | 彩排，记录问题，做视觉和文案小修 | 彩排，修后端阻塞问题，备份示例输出 | 最终交付版 | 只修阻塞和明显体验问题 |

## 5. 每日集成检查点

| 检查点 | 必须看到什么 | 不通过时如何砍范围 |
| --- | --- | --- |
| Day 1 结束 | 能输入 3 章，生成或展示故事圣经 | 如果真实 AI 不稳，用 fixture 演示，后端保留 fake provider |
| Day 2 结束 | 能选择改编策略，生成并下载 YAML | 如果改编计划不稳，先固定高忠实度模板 |
| Day 3 中午 | 能展示至少一条审查 warning 和一条潜台词详情 | 如果 DialogueDoctor 不稳，只展示模型预生成的关键场景 |
| Day 3 最后 | 能完整讲完导入、故事圣经、改编、YAML、审查、导出 | 不再加功能，只修阻塞路径 |

## 6. 两人并行原则

### 成员 A 优先级

1. 先把 demo 用户路径做出来。
2. 用 fixture 先做所有展示面板。
3. 每个后端接口没好之前，都先用 mock 数据。
4. Schema 文档和 demo 讲稿从 Day 2 就开始写。
5. 不做复杂图谱、拖拽编辑、多页面营销首页。

### 成员 B 优先级

1. 先让 pipeline 可运行，再追求生成质量。
2. 每个 skill 都先输出 JSON，再由后端转 YAML。
3. 每一步 artifact 都保存，失败可复用上一步。
4. 先 fake provider，再真实 LLM provider。
5. 不做队列、权限、图数据库、复杂部署。

## 7. Skill 编写顺序

| 顺序 | Skill | 谁主写 | 何时写 | 最小可用标准 |
| --- | --- | --- | --- | --- |
| 1 | NovelReaderSkill | 成员 B 主写，成员 A 提供抽取标准 | Day 1 上午 | 能输出 characters/events/foreshadowing/source_refs |
| 2 | StoryOntologySkill | 成员 B 主写，成员 A 校对人物关系和创作者语感 | Day 1 下午 | 能输出 story_bible、relationship_edges、knowledge_states、voice_profile |
| 3 | AdaptationPlannerSkill | 成员 B 主写，成员 A 提供产品策略文案 | Day 2 上午 | 能输出 retained_events、merged_events、protected_elements、scene_plan |
| 4 | ScreenplayYamlWriterSkill | 成员 B 主写 | Day 2 下午 | 能输出符合 Pydantic 模型的 screenplay JSON |
| 5 | ContinuityAuditorSkill | 成员 B 主写，成员 A 定义 warning 文案 | Day 3 上午 | 能发现缺失 source_refs 和未兑现伏笔 |
| 6 | DialogueDoctorSkill | 成员 A 定义重写方向，成员 B 封装调用 | Day 3 上午/中午 | 能给 1-2 场关键戏补 surface_intent/subtext/action_hint |

## 8. 最推荐的实际推进方式

第一小时不要写代码，先共同锁三份东西：

```text
1. demo_novel_3_chapters.json
2. demo_story_bible.json
3. demo_screenplay.yaml
```

这三份样例就是你们的“并行接口”。你可以拿它们直接搭前端，他可以拿它们直接写模型、校验和导出。只要样例结构稳定，前后端就不会互相堵住。

最终验收按一条路径：

```text
导入 3 章小说
  -> 生成故事圣经
  -> 选择高忠实度 + 保留伏笔
  -> 生成 YAML 剧本
  -> 查看未兑现伏笔 / 潜台词 warning
  -> 下载 YAML + Schema 文档
```

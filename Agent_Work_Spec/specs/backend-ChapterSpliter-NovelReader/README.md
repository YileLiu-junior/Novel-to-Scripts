# ChapterSplitter 与 NovelReader 设计包

本目录定义 `ChapterSplitter._split_by_ai`、`NovelReaderSkill` 调用时机、失败定义、文件级改动计划和验收样例。

核心结论：

- `ChapterSplitter` 是 raw txt intake boundary，负责清洗声明、目录、广告，并识别正文第 1-3 章。
- `ChapterBoundaryReaderSkill` 是轻量 AI boundary planner，只建议切分边界，不提取角色、事件、伏笔，不生成剧本。
- `NovelReaderSkill` 仍在章节保存之后调用，消费已经拥有 `chapter_###` 和 `p_###` 的稳定章节。
- 前端 API 契约不新增“选择章节数量”入口，`POST /api/projects/{project_id}/chapters/auto-split` 响应形状保持 `{chapters, chapter_count, mode_used}`。

文件说明：

- `SPEC.md`：产品与架构设计。
- `IMPLEMENTATION_PLAN.md`：文件级实现计划和测试步骤。
- `ACCEPTANCE.md`：验收标准和失败定义。
- `reference-reuse/novel-analyzer-split.md`：从 `.tmp-novel-to-script-team` 可复用内容拆成两个 backend skill 的说明。
- `split-fixtures/`：正则拆分和 AI 拆分的测试输入/期望输出。


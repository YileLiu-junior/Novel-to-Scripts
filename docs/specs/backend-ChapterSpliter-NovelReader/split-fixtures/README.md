# 拆章测试输入输出样例

这个目录用于人工检查规则拆分和 AI boundary planner 的差异。

目录：

- `inputs/`：raw txt 输入。
- `outputs/rule/`：规则拆分的期望输出。
- `outputs/ai/`：AI boundary planner 的期望输出。
- `outputs/current-bug/`：当前未修复实现可能出现的问题，用于对比。

说明：

- 输出文件是 contract fixture，不代表当前代码已经实现。
- `chapter_id` 和 `paragraph_id` 不在这些输出里生成；它们属于 `ChapterService`。
- AI 输出只包含边界计划，不包含角色、事件、伏笔或剧本内容。


# `.tmp-novel-to-script-team` 可复用内容拆分

来源：

- `.tmp-novel-to-script-team/agents/novel-analyzer.md`
- `.tmp-novel-to-script-team/skills/adaptation-analysis-skill/SKILL.md`

原始可复用职责：

```text
清洗原文并提取核心冲突
判定男频/女频与改编策略
构建角色档案和称呼规范表
```

V0+V1 后端不能把这些职责塞进一个前置 raw txt reader。原因是 source_refs 必须建立在稳定 `chapter_###` 和 `p_###` 之后。

因此拆成两个 backend skill：

| 原职责 | 新归属 | 说明 |
| --- | --- | --- |
| 清洗原文 | `ChapterBoundaryReaderSkill` | 只识别声明、广告、目录、正文起点和前三章边界 |
| 提取核心冲突 | `NovelReaderSkill` | 只在章节 ID 和段落 ID 生成后执行 |
| 判定改编策略 | `NovelReaderSkill` 输出候选字段，`AdaptationPlannerSkill` 消费 | 不在拆章阶段做创作判断 |
| 构建角色档案 | `NovelReaderSkill` + `StoryOntologySkill` | 角色 ID 稳定化由后续 story ontology 完成 |
| 称呼规范表 | V0 进入 `character_candidates` 或 `story_bible.voice_profile`，V2 再扩展 | 不能阻塞当前三章 demo path |
| 一致性锚点 | `NovelReaderSkill.foreshadowing_candidates` 与 `StoryOntologySkill.knowledge_states` | 必须带 source_refs |

## ChapterBoundaryReaderSkill 精简 prompt 原则

角色：

```text
你是小说 raw txt intake 边界识别器，只判断哪些行属于声明/广告/目录/序章/正文主章节。
```

任务：

```text
1. 标记 ignored_spans。
2. 找出正文 main_chapter 的前 3 个候选范围。
3. 为每个范围提供 line number 和 confidence。
4. 不提取故事内容。
```

禁止：

```text
不写剧情分析。
不写角色。
不写冲突。
不写伏笔。
不生成标题。
不改写原文。
```

## NovelReaderSkill 增强原则

`NovelReaderSkill` 可以吸收 `novel-analyzer` 的分析口径，但输出必须是 JSON artifact：

```json
{
  "character_candidates": [],
  "events": [],
  "locations": [],
  "objects": [],
  "foreshadowing_candidates": [],
  "continuity_anchors": []
}
```

每个 event、anchor、foreshadowing candidate 必须带 `source_refs`。推断字段必须标 `evidence_level: inferred`。


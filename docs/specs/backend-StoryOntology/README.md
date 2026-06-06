# Backend StoryOntology 规格索引

本目录记录 `StoryOntologySkill` 从“最小故事圣经”升级为 `Adaptation Evidence`（改编证据层）的需求、规则、执行计划和 prompt reference。

## 文档结构

- `01-adaptation-evidence-requirements.md`：`ce-brainstorm` 产出的需求文档，回答要做什么、为什么做、用户如何感知。
- `02-adaptation-evidence-contract.md`：规则方案与输入输出 contract，定义后端开关、artifact 字段、边界和校验规则。
- `03-implementation-plan.md`：`ce-plan` 产出的具体执行步骤，按 schema、fixture、domain、provider、orchestrator、validator、frontend 和 tests 排序。
- `04-storyontology-skill-prompt-reference.md`：新版 `StoryOntologySkill Prompt Reference`，供后续更新 `backend/app/ai/prompts/story_ontology.md` 时使用。

## 范围提醒

本设计只服务 V0+V1 主链路：

```text
chapters
  -> NovelReaderSkill
  -> StoryOntologySkill
  -> AdaptationPlannerSkill
  -> ScreenplayWriter
  -> validation/export
```

暂不实现独立 `/generate/story-bible` 路由，不引入长集数生产、分镜、生图、hit-script retrieval 或真实 subagent runtime。

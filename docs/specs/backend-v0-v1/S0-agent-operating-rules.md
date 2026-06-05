# S0 Agent 运行规则

## 负责人

Showrunner。

## 目的

在后端工作开始之前，确保所有 agent 遵循统一的产品范围、目录边界、评审关卡和实施顺序。

## 输入

- `docs/plans/2026-06-05-004-project-directory-structure.md`
- `docs/plans/2026-06-05-005-v1-backend-framework-and-agent-team-decision.md`
- `docs/plans/2026-06-05-006-v0-v1-backend-spec-and-agent-team-plan.md`
- `Pre-research/AI小说转剧本MVP方案细化.md`
- `.tmp-novel-to-script-team/references/index.md`
- `.tmp-novel-to-script-team/references/00-first-principles.md`
- `.tmp-novel-to-script-team/references/04-review-gates.md`
- `.tmp-novel-to-script-team/references/21-agent-logging-standard.md`

## 输出

- 根目录 `AGENTS.md`
- 本规范索引：`docs/specs/backend-v0-v1/`

## 规则

- 以 005 作为后端决策依据。
- 以 004 作为目录布局依据。
- `.tmp-novel-to-script-team/references` 仅用于评审关卡、可追溯性、连续性、评审语言和质量纪律。
- 不复制故事板（storyboard）、Seedance、图像生成或长篇流程。
- 在 V0+V1 阶段不引入运行时子 agent。

## 验收标准

- Agent 在阅读 `AGENTS.md` 后，能够知晓 domain、API、prompt、validator、exporter 和 worker 各自应放置的位置。
- V0+V1 的非目标范围已明确声明。
- 评审关卡使用 PASS/FAIL 语言，并附带位置、问题和操作说明。


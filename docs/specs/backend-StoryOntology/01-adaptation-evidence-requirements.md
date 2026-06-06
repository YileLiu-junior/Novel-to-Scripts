---
date: 2026-06-06
topic: backend-storyontology-adaptation-evidence
---

# StoryOntology 改编证据层需求

## Summary

将 `StoryOntologySkill` 从“生成最小 story_bible”升级为可审查的 `Adaptation Evidence`（改编证据层）：它在原文解析之后提取角色、关系、知情差、完整事件、冲突轴和一致性锚点，让用户能看见剧本生成前的结构化依据。

---

## Problem Frame

当前主链路里 `StoryOntologySkill` 已经被调用，也会保存 `story_bible` artifact，但用户主要在最终 `screenplay_json` 里看到角色信息。这个体验容易让 StoryOntology 看起来只是后台中间步骤，无法证明后续剧本是如何从原文事实、冲突、关系和事件完整性推导出来的。

用户真正需要感知的不是“系统多跑了一个 skill”，而是“剧本不是黑盒生成”。当一个 scene 出现时，用户应该能追到它来自哪些原文事件、哪些关系和知情差被保护、哪些事件不能被拆开、哪些信息必须转化为可演、可见、可听的表达。

---

## Actors

- A1. 创作者用户：上传小说章节，检查生成剧本是否忠于原文且可改编。
- A2. 前端开发者：通过 HTTP API 读取 artifact，并在结果页展示改编证据。
- A3. Backend Builder：维护 pipeline、artifact、schema、validator 和 fake provider。
- A4. StoryOntologySkill：在 `NovelReaderSkill` 之后输出 source-grounded evidence，不直接决定改编取舍。
- A5. AdaptationPlannerSkill：消费 StoryOntology 的证据输入，生成改编计划。
- A6. Validation Director：用 deterministic code 校验结构和引用，不评价创作质量。

---

## Key Flows

- F1. 一键生成中的证据链
  - **Trigger:** 用户在已有至少三章章节后点击生成结构化剧本。
  - **Actors:** A1, A2, A3, A4, A5, A6
  - **Steps:** 后端运行主 orchestrator；`StoryOntologySkill` 产出 `story_bible` artifact；planner 和 writer 继续沿同一路径生成；前端结果页读取并展示 evidence sections。
  - **Outcome:** 用户能在最终结果中看到“剧本生成前的改编依据”，而不是只看到最终剧本。
  - **Covered by:** R1, R2, R4, R8

- F2. Fake provider 联调
  - **Trigger:** 环境设置为 `XENGINEER_AI_PROVIDER=fake`。
  - **Actors:** A2, A3, A4
  - **Steps:** Fake provider 根据当前项目章节生成稳定 evidence；artifact 保存到真实项目数据目录；前端按同一 API 读取。
  - **Outcome:** 前端无需 API key，也能看到 StoryOntology 的输入输出效果。
  - **Covered by:** R5, R6, R9

- F3. 证据引用校验
  - **Trigger:** 后端生成或校验 screenplay JSON/YAML。
  - **Actors:** A3, A6
  - **Steps:** Validator 检查 evidence 中的 chapter、event、character、relationship 引用是否存在；错误进入 structured findings 和 audit report。
  - **Outcome:** 断链问题被 deterministic code 发现，用户能定位具体 entity。
  - **Covered by:** R7, R10

---

## Requirements

**产品定位**

- R1. `StoryOntologySkill` 对外展示应定位为 `Adaptation Evidence`（改编证据层），而不是只展示为抽象 ontology。
- R2. 结果页必须让用户看见 StoryOntology 产出的关键 evidence：完整事件、冲突轴、一致性锚点、关系和知情差。
- R3. 面向用户的主命名统一为“改编证据”；`story_bible` 只作为 artifact type、API field 或内部工程 term 使用，不作为主要 UI 文案。

**后端输入输出**

- R4. 后端生成请求应支持一个后端可见的 `adaptation_evidence_mode`，用于控制 StoryOntology 输出 V1.5 改编证据层或 legacy minimal shape；默认启用 enriched evidence，但不能绕过主 pipeline。
- R5. 启用开关后，`story_bible` artifact 必须包含能证明 StoryOntology 参与生成的版本和模式信息。
- R6. Fake provider 和 real provider 必须共享同一 orchestrator path；fake 输出应根据当前章节构造 project-specific evidence。
- R6a. `minimal` 只用于 backend/debug/legacy compatibility，不作为正常用户可见的前端开关。

**结构与校验**

- R7. Evidence 字段必须先进入 schema 和 fixtures，再进入 domain、provider、frontend 或 tests。
- R8. StoryOntology 输出只能描述 source-grounded facts，不能决定 retained、merged、deleted 或 deferred 这些改编操作。
- R9. 旧 artifact 缺少 V1.5 字段时，前端、planner 和 exporter 必须以空 section 或默认值降级，不得失败。
- R10. Validator 只检查结构、ID 格式和引用完整性，不评价冲突强度、爽点质量或对白创作水平。

**Planner 连接**

- R11. V1.5 至少需要一个最小 planner/audit 消费点：标记为完整且不可拆开的 event，不能在 scene plan 中被无依据拆散；否则产生 audit warning。
- R12. Planner 可以参考 evidence，但 adaptation decision 仍写入 `adaptation_plan`，不回写 StoryOntology artifact。

**前端感知**

- R13. 前端应通过 `frontend/api_client.py` 读取 story_bible artifact，view 组件不得散落 API path。
- R14. 关系展示必须兼容 schema 当前的 `relationship_edges[].from` 和 `relationship_edges[].to`，避免关系方向失真。
- R15. 结果页必须支持最小 `scene-to-evidence trace`：从某个 scene 追溯到对应 event、conflict axis、source refs 和 continuity anchor。
- R16. 完整事件展示应体现 planner 对 `must_keep_together` 的消费状态，例如“已保护”“被拆分需说明”或“未关联场景”。

---

## Acceptance Examples

- AE1. **Covers R4, R5.** Given 用户使用默认生成配置，when 生成完成，then `story_bible` artifact 中能看到 `schema_version` 和 `adaptation_evidence_mode`，证明 V1.5 evidence 已启用。
- AE2. **Covers R2, R13.** Given 生成完成并进入结果页，when 用户打开改编证据区域，then 页面展示完整事件、冲突轴、一致性锚点和 source refs，而不是只展示最终剧本。
- AE3. **Covers R8, R12.** Given StoryOntology 输出 `must_keep_together` event，when planner 生成 scene plan，then保留/合并/删除决策仍只出现在 `adaptation_plan`，StoryOntology artifact 不写改编决策。
- AE4. **Covers R7, R10.** Given invalid fixture 中 evidence 引用不存在的 event 或 character，when 运行 deterministic validation，then 返回带 `target_id` 的 finding。
- AE5. **Covers R9.** Given 一个旧项目只有旧版 `story_bible` artifact，when 前端刷新结果页，then evidence sections 显示为空或“暂无”，页面不崩溃。
- AE6. **Covers R15.** Given 用户在结果页打开任一 scene，when 展开“改编证据溯源”，then 能看到关联 event、conflict axis、source refs 和 continuity anchor，而不需要阅读原始 JSON。
- AE7. **Covers R11, R16.** Given 某个 event 标记为 `complete_event=true` 且 `must_keep_together=true`，when 前端展示改编证据，then 该 event 显示 planner 消费状态，并在被拆散或遗漏时引导用户查看 audit warning。

---

## Success Criteria

- 用户能解释 StoryOntology 的作用：它把原文变成可审查的改编证据，而不是直接写剧本。
- Demo 可以指向一个 scene，并追溯到对应 event、conflict axis、source refs 和 continuity anchor。
- Fake provider 模式下不需要真实 API key，也能稳定展示 enriched evidence。
- 断链引用能被 deterministic validator 发现，并写入 audit report。
- 正常用户界面不出现 `minimal` 模式选择；该模式只保留为后端调试和旧数据兼容能力。
- 后续实现人员可以从本目录文档直接进入执行计划，不需要重新发明字段和边界。

---

## Scope Boundaries

- 暂不实现独立 `/generate/story-bible` 或分步工作台。
- 暂不实现长集数 episode production、付费卡点、分镜、图片生成、视频提示词或 hit-script retrieval。
- 暂不引入 Redis、Celery、外部队列、图数据库或真实 subagent runtime。
- 暂不让 StoryOntology 直接决定哪些事件保留、合并、删除或延后。
- 暂不要求 real provider 的输出质量达到最终商业可用；V1.5 先保证结构、traceability 和 fake demo。

---

## Key Decisions

- 使用 `Adaptation Evidence` 作为产品定位：比 “Ontology” 更容易让用户理解其价值。
- 保持主 `/generate/screenplay` pipeline 不变：避免出现第二条 generation path。
- 只引入少量 V1.5 字段：优先完整事件、一致性锚点、冲突轴和可视化表达约束，暂缓更复杂的爽点、反转和长集数结构。
- `adaptation_evidence_mode` 只控制 evidence 丰富程度，不允许跳过 StoryOntology；`minimal` 只作为 backend/debug/legacy compatibility 使用，正常用户界面不暴露。

---

## Dependencies / Assumptions

- `schemas/screenplay.schema.json` 仍是前后端唯一主 contract。
- `ArtifactService` 已能保存并按类型读取 `story_bible` artifact。
- `screenplay.schema.json` 的相关对象允许新增 optional properties，且旧数据可以兼容。
- 前端结果页已经消费 `screenplay_json`，可以小步增加 `story_bible` artifact 快照。

---

## Outstanding Questions

### Deferred to Planning

- [Affects R15][Product] `scene-to-evidence trace` 的首版展示深度是否只做到 scene card 展开区，还是同时在“改编证据”tab 中提供跨场景索引。
- [Affects R11][Technical] `must_keep_together` 的最小校验是在 planner 阶段产生 warning，还是在 validation 阶段统一检查。

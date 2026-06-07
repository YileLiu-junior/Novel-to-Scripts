---
date: 2026-06-07
topic: pipeline-latency-reduction
focus: 减少 LLM 串联调用次数，缩短小说→剧本生成耗时
mode: repo-grounded
---

# Ideation: LLM 管线耗时优化

## Grounding Context

### Codebase Context

- **项目**: XEngineer, Python 3.11+ FastAPI 后端 + Streamlit 前端
- **LLM Provider**: DeepSeek (`deepseek-v4-pro` / `deepseek-v4-flash`)，通过 OpenAI 兼容 SDK
- **核心管线**: `GenerationOrchestrator.run_v1()` — 4 道 LLM 串联调用
- **当前耗时**: 4-10 分钟

### 当前 4 步串行 LLM 管线

```
ChapterBoundaryReader (仅规则不够时触发，轻量)
       │
       ▼
NovelReader        → novel_analysis    (15-30s)
       │
       ▼
StoryOntology      → story_bible       (30-60s) ← 最复杂
       │
       ▼
AdaptationPlanner  → adaptation_plan   (10-20s) ← 最轻量
       │
       ▼
ScreenplayWriter   → screenplay_json   (40-120s) ← 输出最大
       │
       ▼
  归一化 + 校验 (纯代码)
```

### 步骤间依赖关系

- NovelReader → StoryOntology: **强依赖**（后者需要角色候选+事件）
- StoryOntology → AdaptationPlanner: **强依赖**（后者需要故事圣经）
- AdaptationPlanner → ScreenplayWriter: **强依赖**（后者需要改编计划+规范角色/事件表）
- **关键洞察**: 前三步的输入高度重叠（都是章节文本+事件+角色），是"浅读→深读→决策"的递进关系

## Topic Axes

- **步骤合并** — 将多道串行 LLM 调用合并为更少的调用
- **架构裁剪** — 去掉或简化某步的输出要求
- **模型/Token 优化** — 用更小模型、更短 Prompt、更少 Token 加速

## Ranked Ideas

### 1. 两步管线 — "深度分析 + 剧本写作"

**Description:** 将前三个 LLM 步骤（NovelReader → StoryOntology → AdaptationPlanner）合并为一个 "DeepAnalysis" 步骤。在一次 LLM 调用中完成：角色提取、故事圣经构建（关系/知情状态/冲突/因果图）、改编决策（保留/合并/删除事件、场景计划）。第二步 ScreenplayWriter 不变。4 次 LLM 调用 → 2 次。

**Axis:** 步骤合并

**Basis:** `direct:` 当前架构中 NovelReader、StoryOntology、AdaptationPlanner 的输入高度重叠（都是章节文本+事件+角色），且三者之间是严格串行依赖。StoryOntology 的 Prompt（338 行）明确要求"保留所有 upstream_characters、保留所有 upstream_events"，说明这两步本质上是"浅读→深读"的递进关系。AdaptationPlanner 的输出（~1K tokens）信息密度低，模型在"分析"阶段就能顺便做出改编决策。

`direct:` `_normalize_story_bible()` 和 `_normalize_all_references()` 等归一化函数的存在证明代码层能够补偿 LLM 输出的不稳定性，减少步骤后归一化层可以兜底。

**Rationale:**
- 网络往返从 4 次降到 2 次（省 ~30s 延迟）
- 合并后的 Step 1 输入与 StoryOntology 当前输入大小相当（~12K tokens），不会显著增加单步延迟
- 模型内部推理（CoT）比跨 API 调用传递 JSON 更高效——DeepSeek-V4-Pro 的长上下文分析能力可以胜任
- 预估总耗时: 30-60s (深度分析) + 40-90s (剧本写作) = **1.2-2.5 分钟**，相比当前 4-10 分钟缩短 **50-75%**
- 保留 story_bible 作为中间产物（在 Step 1 的输出中），不丢失可检查性

**Downsides:**
- 失去 novel_analysis 和 adaptation_plan 两个独立 artifact 的可检查性
- 合并后的 Prompt 需要精心设计——要求太多可能导致模型丢失细节
- 调试时无法单步重跑中间环节（但可以通过 `save_intermediates` 参数保留 Step 1 的完整输出）
- 单次调用失败 = 三个步骤全失败，无中间 checkpoint 恢复

**Confidence:** 80%

**Complexity:** Medium

**Status:** Unexplored

---

### 2. 合并 AdaptationPlanner → ScreenplayWriter（方案 5 — 已选定执行）

**Description:** 将 AdaptationPlanner 的职责（决定保留/合并/删除事件、编排场景计划）内化到 ScreenplayWriter 的 Prompt 中。4 步 → 3 步。从 4-10 分钟降到约 **3-7 分钟**。

**Axis:** 步骤合并

**Basis:** `direct:` AdaptationPlanner 的输出 token 量很小（~1K），决策逻辑简单（"基于 fidelity_level 和 preserve_priorities 决定保留哪些事件"）。ScreenplayWriter 的 Prompt 已经要求它理解事件表和改编配置。

**Rationale:** 实施最简单——只需修改 ScreenplayWriter 的 Prompt，删除 AdaptationPlanner 调用。场景编排与剧本写作本身就是同一创作行为的不同侧面。

**Downsides:** 独立收益有限（只省 10-20s），但改动最小、风险最低。

**Confidence:** 70%

**Complexity:** Low

**Status:** 已选定执行

---

### 3. 用代码规则替代 StoryOntology 的部分推理

**Description:** StoryOntology 产出的"关系边""知情状态""因果图"可以用代码规则从 NovelReader 的输出中推导。只在规则无法覆盖时调 LLM 补充。

**Axis:** 架构裁剪

**Basis:** `direct:` `_normalize_story_bible()` 和 ReferenceValidator 已在做大量规则推理。

**Rationale:** StoryOntology 是当前最慢的单步（30-60s），砍掉或瘦身直接省掉最大瓶颈。

**Downsides:** 规则引擎开发成本高；"冲突池""可视化表达约束"等创造性内容仍需 LLM。

**Confidence:** 65%

**Complexity:** High

**Status:** Unexplored

---

### 4. 按章节并行 NovelReader，汇总后写作

**Description:** 3 章分别发给 3 个并行 LLM 调用做 NovelReader，汇总合并去重后交给 Writer。

**Axis:** 架构裁剪（并行化变体）

**Basis:** `reasoned:` MapReduce 模式在文本分析中的成熟应用。每章分析互不依赖，天然可并行。

**Rationale:** 3 章并行等待 ≈ 20s（而非串行 45-60s）。

**Downsides:** 跨章节一致性可能丢失；可能触发 API rate limit。

**Confidence:** 60%

**Complexity:** Medium

**Status:** Unexplored

---

### 5. 不同步骤使用不同规格模型

**Description:** 分析步骤用 flash/chat 模型，创作步骤用 pro 模型。方案 1 的自然补充。

**Axis:** 模型/Token 优化

**Basis:** `direct:` `DeepSeekProvider.__init__` 接受 `model` 参数，改造只需修改工厂方法。

**Rationale:** flash 模型分析速度快 2-3×，pro 模型保证写作质量。

**Downsides:** 分析质量可能下降。

**Confidence:** 75%

**Complexity:** Low

**Status:** Unexplored（用户选择暂不使用，保持全流程 pro 模型以保证分析质量）

---

### 6. 一步到位 — 单 Prompt 出剧本

**Description:** 最激进方案：一个超长 System Prompt，输入章节文本，直接输出完整 screenplay JSON。1 次 LLM 调用。

**Axis:** 步骤合并 / 架构裁剪

**Basis:** `reasoned:` 大模型单次推理能力足够处理"阅读理解+创作"的复合任务。

**Rationale:** 网络往返 1 次。预估 60-150s。

**Downsides:** **直接违背 XEngineer 核心设计理念**——失去所有中间产物的可检查性。单次失败则全部失败。输出质量不可控。**不推荐。**

**Confidence:** 40%

**Complexity:** Low（实施简单，风险极高）

**Status:** 不推荐 — 违背"产物优先于文本"的设计哲学

---

## Rejection Summary

| # | Idea | Reason Rejected |
|---|------|-----------------|
| P1 | StoryOntology is the biggest bottleneck | 诊断而非方案，已被方案 1 覆盖 |
| P2 | ScreenplayWriter output instability | 诊断而非方案 |
| P3 | 4 network round-trips are pure waste | 诊断，已被方案 1 覆盖 |
| P8 | NovelReader+StoryOntology are the same thing | 与方案 1 合并 |
| P10 | Cache NovelReader output | 杠杆低，仅省 1/4 时间 |
| P11 | Streaming output | 不减少总耗时，只改善感知 |
| P14 | One-step extreme (duplicate) | 与方案 6 合并 |
| P15 | Keep structure, parallelize | 已被方案 4 覆盖 |

## 执行决策

- **立即执行**: 方案 5（合并 AdaptationPlanner → ScreenplayWriter）— 最小改动、最低风险
- **可选下一步**: 方案 1（两步管线）— 如果方案 5 的改善不够，从 git 恢复本文档继续推进

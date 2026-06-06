# Pipeline Fix Plan — 后端链路去 FakeProvider 及架构加固

**来源:** /plan-eng-review 诊断结论
**日期:** 2026-06-07
**分支:** main
**状态:** 待执行

---

## 问题根因

`XENGINEER_AI_PROVIDER` 默认值为 `"fake"`（`settings.py:39`），导致整条链路：
txt → ChapterIntakeService.auto_split_and_save → GenerationOrchestrator.run_v1 →
NovelReaderSkill → StoryOntologySkill → AdaptationPlanner → ScreenplayWriter

全部由 `FakeProvider`（`fake_provider.py`, 471 行）生成确定性占位符，而非调用真实 AI。
pipeline 静默成功（`job_status=succeeded`），但所有输出都是 "【Fake Provider】" 标记的假数据。

---

## 决策记录

### D1 — 删除 FakeProvider（A: 彻底删除）
**ELI10:** FakeProvider 是生产默认值，471 行代码生成假输出，静默替换真实 AI 调用。
**✅ Pros:**
- 彻底消除"假输出看起来像真输出"的陷阱
- 工厂函数简化为 `deepseek → DeepSeekProvider`，`unknown → raise`
- 测试用标准 Python mock 替代 FakeProvider，mock 输出更可控
**❌ Cons:**
- 11 个测试文件和脚本需要改写
**Effort:** human: ~3h / CC: ~30min

### D2 — 静默成功门禁（A: orchestrator 拒绝非真实 provider）
**ELI10:** `run_v1()` 对 provider 类型零检查，`record_fake_run()` 知道自己跑假的但不报错。
**✅ Pros:**
- 即使将来有人绕过 factory，orchestrator 也会拒绝
- fail loud, fail fast
**❌ Cons:**
- 如果将来确有合法的 dry-run 场景，需要额外条件分支
**Effort:** human: ~10min / CC: ~2min

### D3 — 保持 orchestrator 不分拆（C）
**决定:** 1041 行 orchestrator 不拆 normalization 模块。当前有更高优先级的修复。

### D4 — 减少中间产物（A: 只保存最终 3 个 artifact）
**ELI10:** 一次 run 产生 8+ JSON + YAML 文件，用户不知道哪个是最终输出。
**✅ Pros:**
- artifacts 目录清爽，一眼看到 screenplay YAML
- 减少磁盘占用
**❌ Cons:**
- 调试时需要 `--save-intermediates` flag 多跑一次
**Effort:** human: ~20min / CC: ~8min

### D5 — 统一上下游数据传递（A: 角色/事件来源可追溯）
**ELI10:** NovelReader 提取的角色应该作为 StoryOntology/ScreenplayWriter 的强制性输入，而非仅参考上下文。
**✅ Pros:**
- 消除 skill 间角色/事件来源不一致
- 后续验证层可 trace source_ref
**❌ Cons:**
- 需要重构 skill 间数据契约
**Effort:** human: ~2h / CC: ~20min

### D6 — 去掉占位符自动注入（A: 让 validator 报错而非静默修补）
**ELI10:** `_make_placeholder_scene()` 和 `_ensure_non_empty_arrays()` 在 LLM 产出不足时注入 "待补场景" 等内容，掩盖了真实质量问题。
**✅ Pros:**
- 质量信号清晰：validator 报错 = 真的有问题
- 不会拿到带占位符的假输出
**❌ Cons:**
- LLM 输出不稳定时 pipeline 失败率升高（这是好事——应该 visible）
**Effort:** human: ~30min / CC: ~10min

### D7 — 保持 SkillWrapper 空子类（B: 不变）
**决定:** 4 个空子类（各 10 行）是显式文档——保持现状。

### D8 — 实现真实 LLM Trace（A: 完整记录每次 AI 调用）
**ELI10:** 当前只有 `record_fake_run()` 占位方法，换成真 AI 后调试无迹可寻。
**✅ Pros:**
- 每次 AI 调用 raw_output + token 消耗 + latency 可追溯
- 调试角色识别问题时可看原始 response
**❌ Cons:**
- 需要 DeepSeekProvider 返回 token 计数
**Effort:** human: ~45min / CC: ~10min

### D9 — 先修架构再补测试（B: 推迟 E2E test）
**决定:** 先完成 D1-D8 并用真 AI 验证产出质量，再根据实际输出设计 mock E2E test。

### D10 — 章节文本引用存储（A: 引用替代副本）
**ELI10:** novel_analysis、story_bible、screenplay_json 各存一份完整 chapter text，文本膨胀 O(N×3)。
**✅ Pros:**
- 存储从 O(N×3) 降到 O(N×1)
**❌ Cons:**
- 下游 reader 需要改引用解析代码
**Effort:** human: ~1h / CC: ~15min

---

## 执行任务清单

按优先级排序。P1 阻塞所有后续工作；P2 需在同一分支完成；P3 可后续。

### T1 (P1) — 删除 FakeProvider，改写工厂函数
- **决策依据:** D1 + D2
- **文件:**
  - 删除: `backend/app/ai/providers/fake_provider.py`
  - 修改: `backend/app/ai/providers/factory.py` — 去掉 `"fake"` 分支，`unknown → raise ValueError`
  - 修改: `backend/app/ai/providers/__init__.py` — 移除 FakeProvider export
  - 修改: `backend/app/core/settings.py` — 默认 `provider` 改为 `"deepseek"` 或删除默认值（强制要求显式配置）
  - 修改: `backend/tests/ai/test_ai_providers.py` — 删除 `test_provider_factory_defaults_to_fake`，替换所有 FakeProvider 引用为 unittest.mock
  - 摸底: 所有 import FakeProvider 的文件
- **验证标准:**
  - `pytest tests/ -v` 全部通过
  - 不设 `XENGINEER_AI_PROVIDER` 时 `build_ai_provider()` 抛出清晰错误（而非返回 fake）
  - 设 `XENGINEER_AI_PROVIDER=deepseek` 但不设 API key 时 `build_ai_provider()` 抛出 `AiProviderConfigurationError`
- **Effort:** human: ~3h / CC: ~30min

### T2 (P1) — Orchestrator 启动门禁
- **决策依据:** D2
- **文件:** `backend/app/services/generation_orchestrator.py`
- **改动:** 在 `from_provider_settings()` 或 `run_v1()` 中检查 `provider.name`，非 `"deepseek"` 则 `raise ConfigurationError`
- **验证标准:** 尝试用 mock/non-real provider → raise；DeepSeekProvider → 正常运行
- **Effort:** human: ~10min / CC: ~2min

### T3 (P2) — 减少中间产物
- **决策依据:** D4
- **文件:** `backend/app/services/generation_orchestrator.py`, `backend/app/services/artifact_service.py`
- **改动:**
  - `run_v1()` 默认只保存 `story_bible`, `screenplay_yaml`, `audit_report`
  - 中间产物（`novel_analysis`, `adaptation_plan`, `screenplay_json`, `screenplay_rendered`, `chapter_split_plan`）需要 `--save-intermediates` / `save_intermediates=True` 才落盘
- **验证标准:** 默认 run 后 artifacts/ 只有 3 个文件；带 flag run 后全部保存
- **Effort:** human: ~20min / CC: ~8min

### T4 (P2) — 统一上下游数据契约
- **决策依据:** D5
- **文件:** `backend/app/ai/skills/base.py`, `backend/app/services/generation_orchestrator.py`, `backend/app/ai/prompts/*.md`
- **改动:**
  - NovelReader 输出的 `character_candidates` / `events` 作为 StoryOntology 的强制性 schema 输入
  - StoryOntology 输出的 `story_bible.characters` / `events` 作为 ScreenplayWriter 的强制性 schema 输入
  - 每个角色/事件携带 `source_refs` 追溯链
  - Prompt 更新：显式要求 LLM 保留上游角色列表、不得删除已有角色
- **验证标准:** story_bible 中每个 character 有明确的 `source_refs` 指向 novel_analysis
- **Effort:** human: ~2h / CC: ~20min

### T5 (P2) — 去掉占位符自动注入
- **决策依据:** D6
- **文件:** `backend/app/services/generation_orchestrator.py`
- **改动:**
  - 删除 `_make_placeholder_scene()` 函数（line 688-712）
  - 重写 `_ensure_non_empty_arrays()` → 当数组为空时记录 validation finding 但**不**注入占位内容
  - 或者直接删除 `_ensure_non_empty_arrays()`，让 `ValidationService` 负责报错
- **验证标准:** 传入空 scenes → validator 报错，不在输出中看到 "待补场景"
- **Effort:** human: ~30min / CC: ~10min

### T6 (P2) — 实现真实 LLM Trace
- **决策依据:** D8
- **文件:** `backend/app/services/llm_trace_service.py`, `backend/app/ai/providers/deepseek_provider.py`, `backend/app/services/generation_orchestrator.py`
- **改动:**
  - 删除 `record_fake_run()`
  - 新增 `record_run(job_id, step, provider, model, raw_output_preview, tokens_used, latency_ms)`
  - `DeepSeekProvider.generate_structured()` 返回后自动记录（或由 orchestrator 在每次 skill.run() 后记录）
  - orchestrator 中所有 4 个 skill 调用都记录 trace
- **验证标准:** 每次 AI 调用后在 trace 中可查到 raw_output 摘要 + tokens + latency
- **Effort:** human: ~45min / CC: ~10min

### T7 (P2) — 章节文本引用存储
- **决策依据:** D10
- **文件:** `backend/app/ai/providers/deepseek_provider.py`（prompt rendering），`backend/app/services/generation_orchestrator.py`
- **改动:**
  - 中间 artifact 中 chapters 字段改为只存引用 `{chapter_id, paragraph_range}` 而非完整原文
  - Prompt 渲染时从 chapter index 按引用取原文拼接
  - StoryOntology/NovelReader 输入中不再内嵌完整原文——只传引用 + index 查找
- **验证标准:** story_bible artifact 大小不随章节数线性增长
- **Effort:** human: ~1h / CC: ~15min

### T8 (P3) — Pipeline E2E 测试
- **决策依据:** D9（先修架构，再补测试）
- **前置条件:** T1-T7 完成 + 真 AI 验证输出质量达标
- **Effort:** human: ~1.5h / CC: ~20min

---

## Agent Team 分工

### Team A: Provider Layer（T1, T2）
- **Agent:** `team-a-provider`
- **文件域:** `backend/app/ai/providers/`, `backend/app/core/settings.py`, `backend/app/services/generation_orchestrator.py`
- **Tasks:** T1 → T2（T2 依赖 T1）
- **关键词:** FakeProvider 删除、factory 重构、orchestrator gate

### Team B: Pipeline Quality（T3, T4, T5）
- **Agent:** `team-b-pipeline`
- **文件域:** `backend/app/services/generation_orchestrator.py`, `backend/app/services/artifact_service.py`, `backend/app/ai/skills/base.py`, `backend/app/ai/prompts/`
- **Tasks:** T3 → T5（T4 较复杂，T3/T5 独立于 T4）
- **关键词:** artifact cleanup、data contract、placeholder removal

### Team C: Observability（T6, T7）
- **Agent:** `team-c-observability`
- **文件域:** `backend/app/services/llm_trace_service.py`, `backend/app/ai/providers/deepseek_provider.py`, `backend/app/services/generation_orchestrator.py`
- **Tasks:** T6 → T7（可并行，共享 orchestrator 但改动区域不重叠）
- **关键词:** LLM trace、chapter reference storage

### Team D: Validation（T8, 最终审查）
- **Agent:** `team-d-validation`
- **文件域:** `backend/tests/`
- **Tasks:** T8（在所有 T1-T7 完成后执行）
- **关键词:** E2E pipeline test

---

## 执行纪律

每完成一个 Task 后：

1. **`/tdd`** — 先写测试（如适用），再改代码，确保测试通过
2. **`/Plan-Eng-Review`** — 审查改动是否符合该 Task 的决策依据
   - 审查者确认：改动范围与 Decision Record 一致
   - 审查者确认：没有引入新的架构问题
   - 审查者确认：测试覆盖充分
3. **`pytest tests/ -v`** — 全部通过
4. **`git add` + `git commit`** — 提交消息格式：
   ```
   feat: <Task ID + 简短描述>

   Decision: D<N> — <决策一句话>
   Files: <改动的文件列表>
   Verified: pytest all green + /Plan-Eng-Review passed
   ```
5. **通知用户** → 暂停等待确认 → 继续下一个 Task

---

## 预期结果

完成 T1-T7 后：
- `XENGINEER_AI_PROVIDER` 必须显式设为 `"deepseek"` 才能跑 pipeline
- 设 `XENGINEER_AI_PROVIDER=deepseek` + `DEEPSEEK_API_KEY=<key>` 后，pipeline 调用真实 DeepSeek API
- NovelReader 应提取出真实角色名（如 "若水神君"、"东海水君"、"狐族小女"）
- StoryOntology 基于 NovelReader 的角色列表构建关系图
- ScreenplayWriter 产出真实的文学剧本场景（而非 "【Fake Provider】" 占位符）
- artifacts/ 目录只有 3 个文件（screenplay_yaml + story_bible + audit_report）
- 每次 AI 调用有 trace 记录
- Pipeline 失败时 fail loud（占位符不再掩盖问题）

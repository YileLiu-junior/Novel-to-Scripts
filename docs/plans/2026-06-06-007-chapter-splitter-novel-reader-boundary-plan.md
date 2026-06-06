---
title: ChapterSplitter 与 NovelReader 边界实现计划
status: active
origin:
  - docs/specs/backend-ChapterSpliter-NovelReader/SPEC.md
  - docs/specs/backend-ChapterSpliter-NovelReader/IMPLEMENTATION_PLAN.md
  - docs/specs/backend-ChapterSpliter-NovelReader/ACCEPTANCE.md
  - .tmp-novel-to-script-team/agents/novel-analyzer.md
  - .tmp-novel-to-script-team/skills/adaptation-analysis-skill/SKILL.md
created: 2026-06-06
---

# ChapterSplitter 与 NovelReader 边界实现计划

## 1. 目标

把 `ChapterSplitter._split_by_ai` 从占位实现推进为 V0 增强能力：上传 raw txt 后，后端能忽略声明、广告、目录和序章，默认保存正文第 1-3 章；当规则拆分无法得到 3 个可信正文章节时，调用轻量 `ChapterBoundaryReaderSkill` 只做边界规划。

`NovelReaderSkill` 保持后置，只消费已经由 `ChapterService` 生成稳定 `chapter_###` 和 `p_###` 的章节。

## 2. 范围边界

本计划实现：

- `ChapterSplitter` 规则清洗、正文三章过滤、trace 结构和 AI plan 应用。
- 新增 `ChapterBoundaryReaderSkill` 与 prompt。
- `FakeProvider` 支持 `chapter_boundary_reader`。
- 新增 `ChapterIntakeService` 协调拆章、保存章节和 `chapter_split_plan` artifact。
- `POST /api/projects/{project_id}/chapters/auto-split` 响应形状保持不变。
- `NovelReaderSkill` prompt 明确后置阅读职责。
- 聚焦测试覆盖规则、AI fallback、API contract、artifact trace。

本计划不实现：

- 前端新增选择章节范围入口。
- 第 4-5 章隐藏 context 保存或展示。
- 长剧集规划、分镜、Seedance、hit-script retrieval。
- 真实 subagent runtime。

## 3. 关键决策

1. AI 可以建议章节边界，但不能生成最终章节 ID、段落 ID 或改写正文。
2. 规则拆分成功的标准不是“匹配到章节标题”，而是过滤非正文后得到 3 个可信 `main_chapter`。
3. `_split_by_ai` hard fail 时不伪造三章；少于 3 章继续走现有 `ChapterValidator` 的 `chapters.too_few`。
4. `chapter_split_plan` artifact 用于调试 AI boundary planner，不改变前端主响应。
5. `.tmp-novel-to-script-team` 的 `novel-analyzer` 只复用方法论：清洗归 `ChapterBoundaryReaderSkill`，冲突/角色/一致性锚点归后置 `NovelReaderSkill`。

## 4. 实现单元

### U1: ChapterSplitter trace 与规则过滤

文件：

- `backend/app/services/chapter_splitter.py`
- `backend/tests/services/test_chapter_splitter.py`

测试场景：

- 下载站声明不会成为第一章。
- 目录不会计入正文前三章。
- 楔子/序章不会计入正文前三章。
- 规则不足 3 个可信正文章节时返回 warning。

### U2: ChapterBoundaryReaderSkill 与 FakeProvider

文件：

- `backend/app/ai/skills/chapter_boundary_reader.py`
- `backend/app/ai/prompts/chapter_boundary_reader.md`
- `backend/app/ai/skills/__init__.py`
- `backend/app/ai/providers/fake_provider.py`
- `backend/tests/ai/test_chapter_boundary_reader.py`

测试场景：

- fake provider 返回 `ignored_spans`、`candidate_chapters`、`warnings`。
- skill 不返回角色、事件、冲突、伏笔或剧本内容。

### U3: AI plan 应用与安全校验

文件：

- `backend/app/services/chapter_splitter.py`
- `backend/tests/services/test_chapter_splitter.py`

测试场景：

- 规则不足 3 章时 `mode=auto` 调用 AI。
- AI 行号越界时不保存非法章节。
- AI 范围重叠时返回 `chapter_boundary.overlap` warning。
- AI 仅建议边界，代码负责切片。

### U4: ChapterIntakeService 与 artifact trace

文件：

- `backend/app/services/chapter_intake_service.py`
- `backend/app/domain/artifacts.py`
- `backend/tests/services/test_chapter_intake_service.py`

测试场景：

- `auto_split_and_save` 保存章节并返回 trace。
- AI fallback 或 warning 存在时保存 `chapter_split_plan` artifact。
- `job_id` 可为空，不影响 artifact 查询。

### U5: API contract 和文档

文件：

- `backend/app/api/routes_chapters.py`
- `backend/tests/api/test_chapters_auto_split.py`
- `backend/app/ai/prompts/novel_reader.md`
- `fixtures/前端接入指南.md`
- `BACKEND_UNIMPLEMENTED_VERSION_MAP.md`

测试场景：

- `AutoSplitResponse` 仍只有 `chapters`、`chapter_count`、`mode_used`。
- 带声明文本的自动拆章返回正文第一章作为第一项。
- 生成 smoke path 不因新增 `chapter_split_plan` 影响 artifact 计数。

## 5. 验证命令

聚焦测试：

```powershell
pytest backend/tests/services/test_chapter_splitter.py backend/tests/services/test_chapter_intake_service.py backend/tests/ai/test_chapter_boundary_reader.py backend/tests/api/test_chapters_auto_split.py -q
```

主链路 smoke：

```powershell
pytest backend/tests/test_api_smoke_flow.py -q
```

AI provider contract：

```powershell
pytest backend/tests/ai/test_ai_providers.py -q
```

## 6. 详细执行步骤

逐步实现细节见：

- `docs/specs/backend-ChapterSpliter-NovelReader/IMPLEMENTATION_PLAN.md`


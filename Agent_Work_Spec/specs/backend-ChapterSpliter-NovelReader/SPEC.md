# ChapterSplitter._split_by_ai 与 NovelReader 调用时机 Spec

## 1. 背景

当前 `ChapterSplitter._split_by_ai` 名义上是 AI 拆章，实际没有调用 provider。规则切分失败时，它只按空行粗切或退回单章。更严重的问题是，规则拆分会把 raw txt 开头声明当成第一章，例如：

```text
声明:本书为八零电子书(txt02.com)的用户自网络收集整理制作,仅供预览交流学习使用,版权归原作者和出版社所有,如果喜欢,请支持正版,以下作品内容之版权与本站无任何关系。
```

这个问题不是“没有匹配章节”，而是“切出来的前三章不能被后端证明是正文第 1-3 章”。

## 2. 产品决策

V0+V1 固定处理正文第 1-3 章，不新增前端入口让用户选择章节范围。

`auto-split` 的产品承诺是：

```text
用户粘贴全文
  -> 后端删除或忽略声明/广告/目录
  -> 后端找到正文第 1-3 章
  -> 后端保存 3 个稳定章节
  -> 后续生成链路只消费这些稳定章节
```

第 4-5 章轻读 context 先不进入本次实现。否则会引入隐藏 context 的保存、展示、source_refs 归属和前端解释成本。

## 3. 角色边界

### 3.1 ChapterSplitter

职责：

- 统一换行和基本清洗。
- 用规则识别章节标题。
- 过滤声明、版权、下载站广告、目录、简介等非正文块。
- 在规则结果不可信时调用轻量 AI boundary planner。
- 根据可信边界从原文切片，返回最多 3 个正文 `SplitChapter`。

禁止：

- 不生成 `chapter_###` 或 `p_###`，这些仍由 `ChapterService` 生成。
- 不提取角色、事件、伏笔。
- 不改写正文。

### 3.2 ChapterBoundaryReaderSkill

这是新增轻量 skill，复用 `.tmp-novel-to-script-team` 中 `novel-analyzer` 的“文本清洗”思想，但不复用它的长剧集分析工作流。

输入：

```json
{
  "text_excerpt": "normalized raw text",
  "line_index": [
    {"line": 1, "text": "声明..."},
    {"line": 2, "text": "第一章 雨夜归来"}
  ],
  "target_main_chapters": 3
}
```

输出：

```json
{
  "ignored_spans": [
    {
      "kind": "copyright_notice",
      "start_line": 1,
      "end_line": 1,
      "reason": "下载站声明，不属于正文"
    }
  ],
  "candidate_chapters": [
    {
      "chapter_kind": "main_chapter",
      "title": "第一章 雨夜归来",
      "start_line": 2,
      "end_line": 8,
      "confidence": 0.98
    }
  ],
  "warnings": []
}
```

约束：

- 只做 boundary planning。
- 只能引用输入中存在的行号。
- `title` 必须来自原文行；如果原文没有标题，用空字符串，由代码用首行 excerpt 生成显示标题。
- 不能输出角色、事件、冲突、伏笔、场景或对白。
- 不能把 `prologue`、`preface`、`catalog` 计入 `main_chapter`。

### 3.3 NovelReaderSkill

职责保持后置：

```text
ChapterService 保存章节并生成稳定 ID
  -> NovelReaderSkill 读取 normalized chapters + paragraph IDs
  -> 输出 source-backed story assets
```

`NovelReaderSkill` 可以吸收 `.tmp-novel-to-script-team` 中 `novel-analyzer` 的“冲突/爽点、角色、称呼规范、一致性锚点”思想，但必须压成 V0+V1 的结构化 artifact：

- `character_candidates`
- `events`
- `locations`
- `objects`
- `foreshadowing_candidates`
- `source_refs`

## 4. 失败定义

### 4.1 可恢复问题

这些不算最终失败，应转为 ignored span 或 warning：

- raw txt 开头有版权声明、下载站广告、目录。
- 第一段不是正文，但后续能找到 3 个可信正文主章节。
- 章节编号跳号，但仍能找到 3 个可信正文主章节。

### 4.2 AI fallback 条件

`mode=auto` 下，规则拆分出现以下情况时调用 `ChapterBoundaryReaderSkill`：

- 过滤非正文块后，可信 `main_chapter` 少于 3 个。
- 第一块疑似声明、目录或广告。
- 章节范围出现异常重叠或空正文。
- 章节标题模式不稳定，例如全是纯数字但正文显然包含章回标题。

### 4.3 hard fail

以下情况最终判为拆分失败：

- 规则和 AI 都无法得到 3 个可信 `main_chapter`。
- AI 返回行号越界、范围重叠、正文为空。
- AI 把声明、目录、广告、序章、楔子计为前三章。
- AI 生成不存在于原文的章节标题并要求代码使用。

为了保持前端契约，`auto-split` 不新增错误响应形状。它可以保存少于 3 章，后续 `generate/screenplay` 仍由现有 `ChapterValidator` 返回 `chapters.too_few`。

## 5. Artifact 策略

如果 AI boundary planner 被调用，后端保存 `chapter_split_plan` artifact，`job_id` 可以为空：

```json
{
  "mode_requested": "auto",
  "mode_used": "ai",
  "ignored_spans": [],
  "candidate_chapters": [],
  "warnings": [],
  "source": "ChapterBoundaryReaderSkill"
}
```

如果只走规则成功，可选择保存同类型 artifact，便于调试；但 V0 最小实现只要求 AI fallback 保存。

## 6. 前端契约

不改：

- `AutoSplitRequest`
- `AutoSplitResponse`
- `ChapterInput`
- `PUT /chapters`
- `GET /chapters`
- `POST /chapters/auto-split`

`mode_used` 建议稳定为：

- `rule`
- `ai`
- `rule_with_warnings`
- `failed`

如果担心前端已写死枚举，则 V0 只返回现有 `rule` / `ai`，把 warnings 放进 artifact。


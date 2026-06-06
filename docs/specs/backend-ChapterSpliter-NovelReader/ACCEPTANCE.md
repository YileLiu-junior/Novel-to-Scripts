# 验收标准

## 1. 功能验收

1. 粘贴带下载站声明的全文时，声明不会成为 `chapter_001`。
2. 规则识别到 3 个正文主章节时，`auto-split` 不调用 AI。
3. 规则识别不到 3 个可信正文主章节时，`auto-split` 调用 `ChapterBoundaryReaderSkill`。
4. AI 只返回边界计划，代码负责切片和保存。
5. 保存后的章节 ID 仍为 `chapter_001`、`chapter_002`、`chapter_003`。
6. 保存后的段落 ID 仍为每章内 `p_001`、`p_002`。
7. `NovelReaderSkill` 只消费已保存章节，不消费 raw txt。
8. `generate/screenplay` 的 `novel_reader -> story_ontology -> adaptation_planner -> screenplay_writer` 顺序不变。

## 2. 失败验收

### 2.1 声明误识别

输入包含：

```text
声明:本书为八零电子书(txt02.com)的用户自网络收集整理制作...
第一章 雨夜归来
...
```

期望：

- `ignored_spans[0].kind == "copyright_notice"`。
- `chapters[0].title == "第一章 雨夜归来"`。
- 任何返回或持久化章节中都不出现以 `声明:` 开头的 title。

### 2.2 正文不足

过滤非正文块后只有 2 个 `main_chapter`。

期望：

- `auto-split` 可以保存 2 章。
- `POST /generate/screenplay` 返回 422。
- error finding 包含 `chapters.too_few`。

### 2.3 AI 边界异常

AI 返回重叠范围：

```json
[
  {"start_line": 3, "end_line": 10},
  {"start_line": 8, "end_line": 15}
]
```

期望：

- 丢弃 AI plan。
- 不把重叠切片保存为 3 章。
- `chapter_split_plan` artifact 记录 warning：`chapter_boundary.overlap`。

## 3. 测试验收

必须新增测试：

- `backend/tests/services/test_chapter_splitter.py`
- `backend/tests/services/test_chapter_intake_service.py`
- `backend/tests/ai/test_chapter_boundary_reader.py`
- `backend/tests/api/test_chapters_auto_split.py`

至少覆盖：

- 声明被忽略。
- 目录被忽略。
- 序章不计入正文前三章。
- 规则成功时不调用 AI。
- 规则不足三章时调用 fake AI。
- AI 返回非法行号时失败。
- `AutoSplitResponse` 形状不变。

## 4. 手工验收样例

见 `split-fixtures/`。


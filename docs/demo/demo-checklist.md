# Demo 演示清单

## Demo 故事

本后端是一个结构化的改编工作台。它不是用一个黑盒 prompt 让模型直接输出最终剧本，而是生成可审查的中间产物，并在导出前校验引用关系。

## 数据文件

- 主要 fixture 数据来源：
  `research/novel-to-script-cases/01_sherlock_study_in_pink/`
- 契约 fixture：
  - `fixtures/source_manifest.json`
  - `fixtures/demo_novel_3_chapters.json`
  - `fixtures/demo_story_bible.json`
  - `fixtures/demo_screenplay.json`
  - `fixtures/demo_screenplay.yaml`
  - `fixtures/demo_invalid_refs.yaml`

## 冒烟流程

1. 加载 `fixtures/demo_novel_3_chapters.json`。
2. 创建一个 project。
3. 保存三个 chapter。
4. 用 `FakeProvider` 生成 story bible。
5. 用 `FakeProvider` 生成 adaptation plan。
6. 用 `FakeProvider` 生成 screenplay JSON。
7. 校验引用关系。
8. 导出 YAML。
9. 校验 `fixtures/demo_invalid_refs.yaml` 并展示预期的警告。

## 通过标准

- 不需要真实的 API key。
- 不足三章被拒绝进入生成流程。
- 三章可以进入假生成流程。
- 每一步都保存一个 artifact。
- YAML 能反向解析回 JSON。
- 断裂的引用能产生带 target ID 的 warning 或 error。
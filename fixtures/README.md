# Fixtures 使用说明

`fixtures/` 只用于 demo、mock 和 contract 验证，不是真实项目运行时数据目录。

真实项目数据应写入：

```text
backend/data/projects/{project_id}/
├── project.json
├── chapters/index.json
├── artifacts/index.json
└── jobs/index.json
```

项目级 fixture 放在：

```text
fixtures/projects/{safe_project_name}/
├── demo_novel_3_chapters.json
├── demo_story_bible.json
└── demo_screenplay.json
```

`safe_project_name` 会由项目标题或 project_id 经过文件名安全处理得到。Fake Provider 会优先读取项目级 fixture；如果当前项目没有匹配 fixture，则根据当前项目上传的 chapters 构造项目相关的 fake screenplay，而不会静默返回无关全局 demo。

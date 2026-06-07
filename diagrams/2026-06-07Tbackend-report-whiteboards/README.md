# 后端汇报白板产物说明

本目录包含两张 Raw Grid 主题白板的本地源文件、预览图和飞书 OpenAPI raw JSON。

## 白板 1：汇报方案 + Skill Workflow

- SVG 源文件：`backend-report-skill-workflow.svg`
- PNG 预览：`backend-report-skill-workflow.png`
- 飞书白板 raw JSON：`backend-report-skill-workflow.openapi.json`

内容覆盖：

- 当前后端的汇报主张：不是一次 prompt 写剧本，而是 inspectable adaptation assets。
- 架构设计与产品卖点：schema-first、artifact tracking、job state、validation、YAML/Markdown export。
- Skill 辅助作用：NovelReader、StoryOntology、AdaptationPlanner、ScreenplayWriter。
- Workflow：Project → Chapters → Skills → Screenplay JSON → Validation → Export。
- 汇报讲法：破题、架构、流程、Demo、卖点、边界。

## 白板 2：当前后端架构层设计

- SVG 源文件：`backend-layer-local-store.svg`
- PNG 预览：`backend-layer-local-store.png`
- 飞书白板 raw JSON：`backend-layer-local-store.openapi.json`

内容覆盖：

- API routes、Services、AI Skills、Validators、Exporters、Repositories 的职责边界。
- 当前执行流：`POST generate/screenplay` → `_prepare_generation()` → `enqueue_generation()` → `GenerationOrchestrator.run_v1()` → Normalize / Validate / Export。
- 代码注释中的架构信号：ProjectService、file_store.py、Screenplay 聚合根、CoreElements 索引层、YamlService、workers/jobs.py。
- 当前 persistence 真相源是 project-local file store，不是 SQLite database。
- 本地存储结构：`data/projects/{project_id}/project.json`、`chapters/index.json`、`jobs/index.json`、`artifacts/index.json`、版本化 artifact 文件。

## 已完成检查

```powershell
whiteboard-cli -i .\backend-report-skill-workflow.svg -f svg --check
whiteboard-cli -i .\backend-layer-local-store.svg -f svg --check
```

两张白板均为 `0 errors`。剩余 overlap warnings 是 Raw Grid 硬阴影造成的预期重叠。

## 飞书上传续跑步骤

当前环境的 `lark-cli auth status` 显示 user token missing；上传需要先完成飞书授权。

```powershell
lark-cli auth login --domain "docs,drive" --no-wait --json
```

授权完成后，创建带两个空白白板的飞书文档，并把两个 `.openapi.json` 写入对应 whiteboard token。

示例流程：

```powershell
lark-cli docs +create --api-version v2 --title "XEngineer 后端架构汇报白板" --markdown '<whiteboard type="blank"></whiteboard><whiteboard type="blank"></whiteboard>' --as user

lark-cli whiteboard +update --whiteboard-token <board_token_1> --source '@backend-report-skill-workflow.openapi.json' --input_format raw --overwrite --as user

lark-cli whiteboard +update --whiteboard-token <board_token_2> --source '@backend-layer-local-store.openapi.json' --input_format raw --overwrite --as user
```

如果写入已有非空白白板，必须先 dry run 确认不会误删用户已有内容。

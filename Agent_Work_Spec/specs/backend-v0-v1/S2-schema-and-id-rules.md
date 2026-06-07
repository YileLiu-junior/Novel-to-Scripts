# S2 Schema 与 ID 规则

## 负责人

合约架构师（Contract Architect），协同验证负责人（Validation Director）。

## 目的

定义机器可读的剧本结构（screenplay shape）和稳定的 ID 规则，使交叉引用可被检查验证。

## 文件

- `schemas/screenplay.schema.json`
- `schemas/screenplay.schema.yaml`
- `schemas/screenplay-schema-design.md`
- `backend/app/core/ids.py`
- `docs/schema/screenplay-schema-explained.md`

## ID 规则

- 章节 ID 由后端按顺序分配：`chapter_001`、`chapter_002`。
- 段落 ID 在章节内保持稳定：`p_001`、`p_002`。
- 场景 ID 和台词 ID 由剧本生成或规范化流程产生：`scene_001`、`line_001`。
- 警告 ID 由审计映射分配：`warning_001`。
- 模型建议的角色、事件、关系和伏笔 ID 可在持久化前由后端代码规范化。
- 不得使用数据库自增 ID 作为 YAML 中的公开引用标识。

## Schema 规则

- 顶层必填字段：
  - `schema_version`
  - `project`
  - `source`
  - `adaptation_config`
  - `story_bible`
  - `events`
  - `causal_graph`
  - `foreshadowing`
  - `adaptation_plan`
  - `scenes`
  - `audit_report`
- JSON schema 为规范格式；YAML schema 为其镜像，便于人工阅读。
- Schema 负责检查字段存在性和类型。交叉引用检查由 `backend/app/validators/reference_validator.py` 承担。

## 验收标准

- `demo_screenplay.json` 能够通过 JSON schema 结构校验。
- `demo_screenplay.yaml` 与 JSON 版本结构一致。
- 断裂的引用（broken references）不会被 schema 掩盖，而是由验证器发现并纰漏。


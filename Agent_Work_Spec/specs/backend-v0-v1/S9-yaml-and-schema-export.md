# S9 YAML 与 Schema Export

## 负责人

后端构建者（Backend Builder），协同验证负责人（Validation Director）。

## 目的

产出可见、可 review 的 competition/demo assets，同时让内部事实标准继续保持在 JSON/Pydantic 中。

## 文件

- `backend/app/exporters/yaml_exporter.py`
- `backend/app/exporters/schema_exporter.py`
- `backend/app/services/yaml_service.py`
- `backend/app/services/schema_service.py`
- `schemas/screenplay.schema.json`
- `schemas/screenplay.schema.yaml`
- `docs/schema/screenplay-schema-explained.md`

## 规则

- Exporters 只序列化已经 validation 通过的结构。
- Exporters 不补齐 missing fields。
- Exporters 不 repair model output。
- 用户编辑过的 YAML 必须先 parse 回 JSON，再进入 validation。

## 验收标准

- YAML export 可以 parse 回 JSON。
- YAML validation 返回 findings。
- 缺少 `screenplay_json` 时，download 返回清晰 error。

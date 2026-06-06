# S6 Validator

## 负责人

验证负责人（Validation Director）。

## 目的

用 deterministic code 建立结构可信度，而不是要求 model 自己判断自己的输出是否正确。

## 文件

- `backend/app/validators/chapter_validator.py`
- `backend/app/validators/schema_validator.py`
- `backend/app/validators/reference_validator.py`
- `backend/app/validators/audit_validator.py`
- `backend/app/services/validation_service.py`

## 规则

- Validators 不调用 models。
- Validators 不调用 network APIs。
- Validators 应该仅依赖 fixtures 就能测试。
- Schema validation 检查 shape。
- Reference validation 检查跨实体引用完整性。
- Audit validation 将 findings 映射为用户可见 warnings。

## 最小检查

- `source_refs.chapter_id` 必须存在。
- `scene.characters[]` 必须存在于 `story_bible.characters`。
- `dialogue.character_id` 必须属于当前 scene characters。
- `related_events[]` 必须存在于 `events`。
- `causal_graph.edges.from/to` 必须存在于 `events`。
- `foreshadowing.setup_event_id` 必须存在。
- `foreshadowing.payoff_scene_id` 如果设置，必须存在于 `scenes`。

## 验收标准

- 缺失 character references 时返回 error。
- 缺失 event references 时，根据 severity 返回 warning 或 error。
- `fixtures/demo_invalid_refs.yaml` 触发预期 findings。

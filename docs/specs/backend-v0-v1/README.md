# Backend V0+V1 规范索引

本目录包含 V0+V1 backend 的小步规范文档。上游计划曾称其为“10 个小规范”，但这里保留 `S0` 到 `S10` 的编号：`S0` 是 agent operating rules 的前置检查，`S1` 到 `S10` 是面向实现的规范。

## 执行顺序

1. `S0-agent-operating-rules.md`
2. `S1-fixture-contract.md`
3. `S2-schema-and-id-rules.md`
4. `S3-domain-models.md`
5. `S4-api-dto-and-router.md`
6. `S5-persistence-and-artifacts.md`
7. `S6-validator.md`
8. `S7-ai-provider-and-skill-contract.md`
9. `S8-orchestrator-and-worker.md`
10. `S9-yaml-and-schema-export.md`
11. `S10-smoke-and-acceptance.md`

## 验收规则

每个规范都必须留下可检验的产出物。一个步骤不能仅因为定义了一个 `prompt` 或 `route` 就算完成；它还必须具备与该步骤匹配的测试夹具（fixture）、数据模式（schema）、代码边界、测试目标或 demo 证明。

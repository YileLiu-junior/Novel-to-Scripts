# S10 Smoke 与 Acceptance

## 负责人

评审负责人（Review Director），协同演示制作人（Demo Producer）。

## 目的

证明 backend 在没有 real API key 的情况下，也能支撑 frontend 和 demo 需要。

## 文件

- `scripts/run_demo_smoke.py`
- `scripts/validate_fixtures.py`
- `docs/demo/demo-checklist.md`
- `docs/api/api-contract.md`

## Smoke 路径

```text
read fixtures/demo_novel_3_chapters.json
  -> create project
  -> save chapters
  -> fake generate story_bible
  -> fake generate adaptation_plan
  -> fake generate screenplay_json
  -> validate references
  -> export demo_screenplay.yaml
  -> validate demo_invalid_refs.yaml warnings
```

## 验收标准

- Smoke path 不需要 real API key 即可运行。
- Output YAML 可读且可解析。
- 至少一个 warning 指向具体 scene、dialogue 或 event。
- Demo story 能解释产品是 structured adaptation workbench，而不是 black-box prompt wrapper。

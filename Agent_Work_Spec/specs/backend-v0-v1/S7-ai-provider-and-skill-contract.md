# S7 AI Provider 与 Skill Contract

## 负责人

技能工程师（Skill Engineer）。

## 目的

把 prompts 和 model calls 限定在 AI layer 内，同时让 fake generation 足够稳定，支撑 backend 和 frontend development。

## 文件

- `backend/app/ai/providers/base.py`
- `backend/app/ai/providers/fake_provider.py`
- `backend/app/ai/providers/openai_provider.py`
- `backend/app/ai/skills/README.md`
- `backend/app/ai/skills/novel_reader.py`
- `backend/app/ai/skills/story_ontology.py`
- `backend/app/ai/skills/adaptation_planner.py`
- `backend/app/ai/skills/screenplay_writer.py`
- `backend/app/ai/skills/continuity_auditor.py`
- `backend/app/ai/skills/dialogue_doctor.py`
- `backend/app/ai/prompts/*.md`

## V0+V1 必需项

- `FakeProvider`
- `NovelReaderSkill` minimal wrapper
- `StoryOntologySkill` minimal wrapper
- `AdaptationPlannerSkill`
- `ScreenplayYamlWriterSkill`

## 占位项

- `OpenAIProvider`
- `ContinuityAuditorSkill`
- `DialogueDoctorSkill`

## 规则

- Skill wrappers 接收 structured input，并返回 structured output。
- Skill wrappers 不保存 database records。
- Skill wrappers 不决定 job state。
- Prompt text 放在 `backend/app/ai/prompts/`。
- Business services 不得直接 import real model SDKs。

## 验收标准

- Fake provider 对相同 inputs 返回 deterministic output。
- Skill output 缺失 required fields 时，orchestrator 可以失败并暴露错误。
- Fake provider 和 real provider 适配同一个 provider interface。

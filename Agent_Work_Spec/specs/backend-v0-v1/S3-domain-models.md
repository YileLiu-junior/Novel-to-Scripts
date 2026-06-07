# S3 Domain 模型

## 负责人

后端构建者（Backend Builder）。

## 目的

fixtures 和 schema 通过 Pydantic 模型转化为后端内部的事实标准。

## 文件

- `backend/app/domain/common.py`
- `backend/app/domain/project.py`
- `backend/app/domain/source.py`
- `backend/app/domain/story_bible.py`
- `backend/app/domain/adaptation.py`
- `backend/app/domain/screenplay.py`
- `backend/app/domain/audit.py`
- `backend/app/domain/artifacts.py`
- `backend/app/domain/jobs.py`
- `backend/app/domain/llm_runs.py`
- `backend/app/core/ids.py`

## 规则

- `domain/` 仅允许导入 Pydantic 和标准库。
- `domain/` 不得导入 FastAPI、SQLAlchemy、OpenAI SDK 或 repository 层。
- Domain 模型只表达数据结构，不表达持久化行为。
- 后端生成的 ID 以字符串表示，并具有文档化的前缀。

## 测试

- `backend/tests/services/test_chapter_service.py`
- `backend/tests/validators/test_schema_validator.py`

## 验收标准

- 三章内容规范化为 `chapter_001` 至 `chapter_003`。
- 相同的章节文本再次保存时，段落 ID 保持可预测、不发生变化。
- 缺失必填字段时 Pydantic 校验报错。


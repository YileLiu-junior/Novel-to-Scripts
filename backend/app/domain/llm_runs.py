from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

# llm_runs.py — LLM 调用记录

#   LlmRun 记录每次 LLM 调用的 provider、model、prompt_version、原始输出、解析结果、校验错误——完整的调用链可追溯。
class LlmRun(BaseModel):
    id: str
    job_id: str
    step: str
    provider: str
    model_name: str | None = None
    prompt_version: str | None = None
    raw_output: str | None = None
    parsed_output: dict[str, Any] | None = None
    validation_errors: list[str] = Field(default_factory=list)
    duration_ms: float | None = None
    tokens_used: int | None = None


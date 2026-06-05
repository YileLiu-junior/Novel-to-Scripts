from __future__ import annotations

from typing import Any

from app.domain.llm_runs import LlmRun


class LlmTraceService:
    def record_fake_run(self, job_id: str, step: str, parsed_output: dict[str, Any]) -> LlmRun:
        return LlmRun(
            id=f"llm_{job_id}_{step}",
            job_id=job_id,
            step=step,
            provider="fake",
            model_name="fake-provider",
            parsed_output=parsed_output,
        )


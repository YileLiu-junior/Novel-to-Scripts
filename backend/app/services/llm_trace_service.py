from __future__ import annotations

from app.domain.llm_runs import LlmRun


class LlmTraceService:
    def record_run(
        self,
        job_id: str,
        step: str,
        provider_name: str,
        model_name: str,
        *,
        raw_output: str | None = None,
        duration_ms: float | None = None,
        tokens_used: int | None = None,
    ) -> LlmRun:
        return LlmRun(
            id=f"llm_{job_id}_{step}",
            job_id=job_id,
            step=step,
            provider=provider_name,
            model_name=model_name,
            raw_output=raw_output,
            duration_ms=duration_ms,
            tokens_used=tokens_used,
        )


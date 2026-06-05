from __future__ import annotations

from app.domain.llm_runs import LlmRun


class LlmRunRepository:
    def save(self, run: LlmRun) -> LlmRun:
        return run


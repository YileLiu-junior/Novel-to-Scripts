from __future__ import annotations

import unittest

from app.services.llm_trace_service import LlmTraceService


class LlmTraceServiceTest(unittest.TestCase):
    def test_record_fake_run_is_removed(self) -> None:
        """D8: record_fake_run must not exist."""
        self.assertFalse(
            hasattr(LlmTraceService, "record_fake_run"),
            "record_fake_run should be deleted per D8",
        )

    def test_record_run_exists_and_accepts_real_trace_data(self) -> None:
        """D8: record_run must exist and accept duration_ms + tokens_used."""
        self.assertTrue(
            hasattr(LlmTraceService, "record_run"),
            "record_run must exist per D8",
        )
        svc = LlmTraceService()
        run = svc.record_run(
            job_id="job_001",
            step="novel_reader",
            provider_name="deepseek",
            model_name="deepseek-v4-flash",
            raw_output='{"characters":[]}',
            duration_ms=1234.5,
            tokens_used=1500,
        )
        self.assertEqual(run.job_id, "job_001")
        self.assertEqual(run.step, "novel_reader")
        self.assertEqual(run.provider, "deepseek")
        self.assertEqual(run.model_name, "deepseek-v4-flash")
        self.assertEqual(run.raw_output, '{"characters":[]}')
        self.assertEqual(run.duration_ms, 1234.5)
        self.assertEqual(run.tokens_used, 1500)

    def test_record_run_tokens_and_duration_are_optional(self) -> None:
        """D8: tokens_used and duration_ms can be None."""
        svc = LlmTraceService()
        run = svc.record_run(
            job_id="job_001",
            step="story_ontology",
            provider_name="deepseek",
            model_name="deepseek-v4-flash",
        )
        self.assertIsNone(run.duration_ms)
        self.assertIsNone(run.tokens_used)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = ROOT / "backend"
sys.path.insert(0, str(BACKEND_ROOT))

from app.ai.providers.base import AiProviderConfigurationError, AiProviderResponseError, StructuredGenerationRequest
from app.ai.providers.factory import build_ai_provider
from app.core.settings import load_ai_settings


def main() -> int:
    parser = argparse.ArgumentParser(description="Check the configured XEngineer LLM provider.")
    parser.add_argument(
        "--provider",
        choices=["fake", "deepseek"],
        default=os.getenv("XENGINEER_AI_PROVIDER", "fake"),
    )
    parser.add_argument("--model", default=os.getenv("XENGINEER_DEEPSEEK_MODEL") or os.getenv("DEEPSEEK_MODEL"))
    args = parser.parse_args()

    env = dict(os.environ)
    env["XENGINEER_AI_PROVIDER"] = args.provider
    if args.model and args.provider == "deepseek":
        env["XENGINEER_DEEPSEEK_MODEL"] = args.model

    settings = load_ai_settings(env)
    try:
        provider = build_ai_provider(settings, fixtures={"novel_reader": {"ok": True, "provider": "fake"}})
    except AiProviderConfigurationError as exc:
        print(f"LLM provider configuration error: {exc}", file=sys.stderr)
        return 2

    try:
        result = provider.generate_structured(
            StructuredGenerationRequest(
                skill_name="novel_reader",
                prompt_name="novel_reader.md",
                input_data={
                    "chapters": [
                        {
                            "id": "chapter_001",
                            "title": "Probe",
                            "paragraphs": [{"id": "p_001", "summary": "A backend probe."}],
                        }
                    ]
                },
                temperature=0.0,
                max_tokens=300,
            )
        )
    except AiProviderResponseError as exc:
        print(f"LLM provider request error: {exc}", file=sys.stderr)
        return 3

    print(json.dumps({"provider": result.provider, "parsed_output": result.parsed_output}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

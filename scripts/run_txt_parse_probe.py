from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = ROOT / "backend"
sys.path.insert(0, str(BACKEND_ROOT))

from app.ai.providers.base import AiProviderConfigurationError, AiProviderResponseError
from app.ai.providers.factory import build_ai_provider
from app.ai.skills.novel_reader import NovelReaderSkill
from app.core.settings import load_ai_settings
from app.services.chapter_service import ChapterService


def split_markdown_sections(text: str) -> list[dict[str, str]]:
    matches = list(re.finditer(r"^###\s*(.+?)\s*$", text, flags=re.MULTILINE))
    if not matches:
        return [{"title": "Chapter 1", "text": text.strip()}]

    sections: list[dict[str, str]] = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        if body:
            sections.append({"title": match.group(1).strip(), "text": body})
    return sections


def truncate_sections(
    sections: list[dict[str, str]],
    max_sections: int,
    max_chars_per_section: int,
) -> list[dict[str, str]]:
    selected = sections[:max_sections]
    return [
        {
            "title": section["title"],
            "text": section["text"][:max_chars_per_section],
        }
        for section in selected
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a real TXT novel parsing probe through NovelReaderSkill.")
    parser.add_argument("input", help="Path to a UTF-8 TXT novel file.")
    parser.add_argument("--provider", choices=["fake", "deepseek"], default="deepseek")
    parser.add_argument("--max-sections", type=int, default=3)
    parser.add_argument("--max-chars-per-section", type=int, default=2500)
    parser.add_argument("--output", help="Optional JSON file path for the parsed result.")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.is_absolute():
        input_path = ROOT / input_path
    text = input_path.read_text(encoding="utf-8")
    sections = truncate_sections(
        split_markdown_sections(text),
        max_sections=args.max_sections,
        max_chars_per_section=args.max_chars_per_section,
    )

    chapters = ChapterService().normalize_chapters(sections)
    normalized = [
        {
            "id": chapter.id,
            "title": chapter.title,
            "paragraphs": [
                {"id": paragraph.id, "summary": paragraph.text[:300]}
                for paragraph in chapter.paragraphs
            ],
        }
        for chapter in chapters
    ]

    if args.provider == "fake":
        fixtures = {
            "novel_reader": {
                "characters": [],
                "events": [],
                "foreshadowing_candidates": [],
                "source_refs": [],
            }
        }
    else:
        fixtures = None

    try:
        env = dict(os.environ)
        env["XENGINEER_AI_PROVIDER"] = args.provider
        provider = build_ai_provider(load_ai_settings(env), fixtures=fixtures)
        if provider.name != args.provider:
            raise AiProviderConfigurationError(
                f"Configured provider is {provider.name}, but --provider {args.provider} was requested"
            )
        result = NovelReaderSkill(provider).run({"chapters": normalized})
    except (AiProviderConfigurationError, AiProviderResponseError, ValueError) as exc:
        print(f"TXT parse probe failed: {exc}", file=sys.stderr)
        return 2

    payload = {
        "input": str(input_path),
        "provider": provider.name,
        "sections_used": [{"id": chapter["id"], "title": chapter["title"]} for chapter in normalized],
        "parsed_output": result,
    }

    if args.output:
        output_path = Path(args.output)
        if not output_path.is_absolute():
            output_path = ROOT / output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Wrote {output_path}")

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

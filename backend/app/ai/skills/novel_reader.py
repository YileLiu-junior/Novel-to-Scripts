from __future__ import annotations

from app.ai.skills.base import SkillWrapper


class NovelReaderSkill(SkillWrapper):
    skill_name = "novel_reader"
    prompt_name = "novel_reader.md"


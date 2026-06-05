from __future__ import annotations

from app.ai.skills.base import SkillWrapper


class ScreenplayYamlWriterSkill(SkillWrapper):
    skill_name = "screenplay_writer"
    prompt_name = "screenplay_writer.md"


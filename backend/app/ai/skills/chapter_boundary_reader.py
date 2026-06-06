from __future__ import annotations

from app.ai.skills.base import SkillWrapper


class ChapterBoundaryReaderSkill(SkillWrapper):
    """AI raw txt 边界识别 skill，只建议章节范围，不提取故事资产。"""

    skill_name = "chapter_boundary_reader"
    prompt_name = "chapter_boundary_reader.md"


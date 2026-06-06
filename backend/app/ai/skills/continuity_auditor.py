from __future__ import annotations

from app.ai.skills.base import SkillWrapper


class ContinuityAuditorSkill(SkillWrapper):
    skill_name = "continuity_auditor"
    prompt_name = "continuity_auditor.md"


from __future__ import annotations

from app.ai.skills.base import SkillWrapper


class AdaptationPlannerSkill(SkillWrapper):
    skill_name = "adaptation_planner"
    prompt_name = "adaptation_planner.md"


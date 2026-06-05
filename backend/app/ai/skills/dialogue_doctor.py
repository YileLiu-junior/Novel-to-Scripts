from __future__ import annotations

from app.ai.skills.base import SkillWrapper


class DialogueDoctorSkill(SkillWrapper):
    skill_name = "dialogue_doctor"
    prompt_name = "dialogue_doctor.md"


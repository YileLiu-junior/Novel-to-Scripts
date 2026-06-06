from __future__ import annotations

from app.ai.skills.base import SkillWrapper


class StoryOntologySkill(SkillWrapper):
    skill_name = "story_ontology"
    prompt_name = "story_ontology.md"


from __future__ import annotations

from pydantic import BaseModel, Field

from app.domain.common import SourceRef, VoiceProfile

# 故事圣经（叙事要素提取）：它是 LLM 做叙事分析后的结构化输出：

# Character 角色名、别名、叙事角色、目标、语态、出处引用 
class Character(BaseModel):
    id: str
    name: str
    aliases: list[str] = Field(default_factory=list)
    narrative_role: str | None = None
    goals: dict[str, str] = Field(default_factory=dict)
    voice_profile: VoiceProfile | None = None
    source_refs: list[SourceRef] = Field(default_factory=list)

#角色间关系（类型、当前状态、证据等级） 
class RelationshipEdge(BaseModel):
    id: str
    from_: str = Field(alias="from")
    to: str
    type: str
    current_state: str | None = None
    evidence_level: str | None = None
    source_refs: list[SourceRef] = Field(default_factory=list)

# 角色知情状态（知道什么 / 不知道什么）
class KnowledgeState(BaseModel):
    character_id: str
    knows: list[str] = Field(default_factory=list)
    does_not_know: list[str] = Field(default_factory=list)

# 汇总上述三者
class StoryBible(BaseModel):
    characters: list[Character] = Field(default_factory=list)
    relationship_edges: list[RelationshipEdge] = Field(default_factory=list)
    knowledge_states: list[KnowledgeState] = Field(default_factory=list)

# 叙事事件（类型、参与者、摘要）  
class Event(BaseModel):
    id: str
    title: str
    event_type: str
    participants: list[str] = Field(default_factory=list)
    summary: str
    source_refs: list[SourceRef] = Field(default_factory=list)

# 事件的因果链条
class CausalEdge(BaseModel):
    from_: str = Field(alias="from")
    to: str
    relation: str
    explanation: str

# 伏笔（setup → payoff，含状态追踪）
class CausalGraph(BaseModel):
    edges: list[CausalEdge] = Field(default_factory=list)


class Foreshadowing(BaseModel):
    id: str
    setup_event_id: str
    payoff_event_id: str | None = None
    payoff_scene_id: str | None = None
    status: str = "candidate"
    description: str


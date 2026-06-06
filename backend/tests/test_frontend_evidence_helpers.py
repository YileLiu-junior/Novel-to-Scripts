from __future__ import annotations

from frontend import backend_types as bt


def _screenplay() -> dict:
    return {
        "events": [
            {
                "id": "event_001",
                "title": "完整会面",
                "event_type": "setup",
                "summary": "角色完成一次不可拆分的会面。",
                "complete_event": True,
                "must_keep_together": True,
                "event_flow": ["抵达", "交谈", "达成决定"],
                "conflict_axis": "安顿需求 vs 合租风险",
                "source_refs": [{"chapter_id": "chapter_001", "paragraph_range": "p_001-p_003"}],
            }
        ],
        "story_bible": {
            "relationship_edges": [],
            "knowledge_states": [],
            "continuity_anchors": [
                {
                    "id": "anchor_001",
                    "anchor_type": "relationship_state",
                    "summary": "两人关系仍保持试探距离。",
                    "applies_to": ["char_001", "char_002"],
                    "source_refs": [{"chapter_id": "chapter_001"}],
                }
            ],
            "dramatic_assets": {
                "conflict_pool": [
                    {
                        "id": "conflict_001",
                        "conflict_axis": "安顿需求 vs 合租风险",
                        "participants": ["char_001", "char_002"],
                        "related_events": ["event_001"],
                        "source_refs": [{"chapter_id": "chapter_001"}],
                    }
                ],
                "filmic_constraints": [],
            },
        },
        "adaptation_plan": {
            "scene_plan": [{"scene_id": "scene_001", "purpose": "保留完整会面", "source_events": ["event_001"]}]
        },
    }


def test_event_planner_status_marks_protected_split_and_unlinked() -> None:
    screenplay = _screenplay()
    event = screenplay["events"][0]

    assert bt.event_planner_status(event, screenplay["adaptation_plan"]) == "已保护"

    split_plan = {"scene_plan": [{"source_events": ["event_001"]}, {"source_events": ["event_001"]}]}
    assert bt.event_planner_status(event, split_plan) == "被拆分需说明"

    assert bt.event_planner_status(event, {"scene_plan": []}) == "未关联场景"


def test_scene_evidence_trace_derives_events_conflicts_refs_and_anchors() -> None:
    screenplay = _screenplay()
    scene = {
        "id": "scene_001",
        "related_events": ["event_001"],
        "source_refs": [{"chapter_id": "chapter_001", "paragraph_range": "p_001-p_003"}],
    }

    trace = bt.scene_evidence_trace(scene, screenplay)

    assert trace["events"][0]["id"] == "event_001"
    assert trace["conflicts"][0]["id"] == "conflict_001"
    assert trace["continuity_anchors"][0]["id"] == "anchor_001"
    assert trace["source_refs_text"] == "chapter_001 p_001-p_003"


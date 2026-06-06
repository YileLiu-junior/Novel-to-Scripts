"""Debug: capture raw DeepSeek screenplay_writer output."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

os.environ["XENGINEER_AI_PROVIDER"] = "deepseek"
os.environ["XENGINEER_DEEPSEEK_MODEL"] = "deepseek-v4-flash"
os.environ["DEEPSEEK_BASE_URL"] = "https://api.deepseek.com"

deepseek_api_key = os.environ.get("DEEPSEEK_API_KEY")
if not deepseek_api_key:
    raise RuntimeError("DEEPSEEK_API_KEY must be set before running this debug script.")

from app.ai.providers.deepseek_provider import DeepSeekProvider
from app.ai.skills.screenplay_writer import ScreenplayYamlWriterSkill

provider = DeepSeekProvider(
    model="deepseek-v4-flash",
    api_key=deepseek_api_key,
    base_url="https://api.deepseek.com",
    timeout_seconds=120,
)

# Simulate what story_ontology would output
story_assets = {
    "story_bible": {
        "characters": [
            {"id": "char_001", "name": "Lin", "role": "protagonist"},
            {"id": "char_002", "name": "Old Man", "role": "mentor"},
        ]
    },
    "events": [
        {"id": "evt_001", "title": "Arrival", "description": "Lin arrives at the mysterious town."},
        {"id": "evt_002", "title": "Market Discovery", "description": "Lin notices something wrong in the market."},
        {"id": "evt_003", "title": "The Letter", "description": "Lin finds a mysterious letter."},
    ],
    "causal_graph": {"edges": [{"from": "evt_001", "to": "evt_002"}, {"from": "evt_002", "to": "evt_003"}]},
    "foreshadowing": [],
}

adaptation_plan = {
    "retained_events": ["evt_001", "evt_002", "evt_003"],
    "merged_events": [],
    "deleted_or_deferred_events": [],
    "protected_elements": [],
    "scene_plan": [
        {"scene_id": "scene_001", "source_events": ["evt_001"], "location": "Train Station", "characters": ["char_001"]},
        {"scene_id": "scene_002", "source_events": ["evt_002"], "location": "Market Square", "characters": ["char_001", "char_002"]},
        {"scene_id": "scene_003", "source_events": ["evt_003"], "location": "Town Bench", "characters": ["char_001"]},
    ],
}

adaptation_config = {"target_format": "web_series", "episode_count": 1, "target_duration_min": 10}

sw = ScreenplayYamlWriterSkill(provider)
try:
    screenplay = sw.run({
        **story_assets,
        "adaptation_config": adaptation_config,
        "adaptation_plan": adaptation_plan,
    })

    # Save raw output for inspection
    out_path = Path(os.environ["TEMP"]) / "deepseek_screenplay_debug.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(screenplay, f, ensure_ascii=False, indent=2)
    print(f"Raw output saved to: {out_path}")

    # Print top-level keys and types
    print(f"\nTop-level keys ({len(screenplay)}):")
    for key, value in screenplay.items():
        if isinstance(value, list):
            print(f"  {key}: list[{len(value)}]")
            if value:
                first = value[0]
                if isinstance(first, dict):
                    print(f"    first item keys: {list(first.keys())[:8]}")
                else:
                    print(f"    first item type: {type(first).__name__} = {repr(first)[:100]}")
        elif isinstance(value, dict):
            print(f"  {key}: dict keys={list(value.keys())[:8]}")
        elif isinstance(value, str):
            print(f"  {key}: str = {value[:100]}")
        else:
            print(f"  {key}: {type(value).__name__} = {repr(value)[:100]}")

    # Check scenes structure
    scenes = screenplay.get("scenes", [])
    print(f"\nScenes: {len(scenes)}")
    for i, scene in enumerate(scenes[:3]):
        if isinstance(scene, dict):
            print(f"  [{i}] keys={list(scene.keys())[:12]}")
            for k, v in scene.items():
                if isinstance(v, list):
                    print(f"      {k}: list[{len(v)}]")
                elif isinstance(v, str):
                    print(f"      {k}: str({len(v)})={v[:60]}")
        else:
            print(f"  [{i}] type={type(scene).__name__}: {repr(scene)[:200]}")

except Exception as exc:
    import traceback
    traceback.print_exc()

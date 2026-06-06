"""Verify _resolve_char_id fix for P&P E2E."""
import json, sys
sys.path.insert(0, '.')
from app.services.generation_orchestrator import (
    _build_character_lookup, _normalize_all_references,
    _build_event_lookup, _resolve_char_id
)

path = "F:/Program Files/XEngineer/data/projects/E2E-PP-0607-0543/artifacts/screenplay_json_v001.json"
data = json.loads(open(path, "r", encoding="utf-8").read())

e5 = data["events"][5]
print("BEFORE:")
print(f"  participants: {e5['participants']}")

char_lookup = _build_character_lookup(data["story_bible"])
event_lookup = _build_event_lookup(data["events"])

print()
print("Resolution tests:")
r1 = _resolve_char_id("查尔斯·彬格莱", char_lookup)
r2 = _resolve_char_id("傲慢与偏见", char_lookup)
print(f"  '查尔斯·彬格莱' -> {r1}")
print(f"  '傲慢与偏见' -> {r2}")

data = _normalize_all_references(data, char_lookup, event_lookup)
e5 = data["events"][5]
print()
print("AFTER:")
print(f"  participants: {e5['participants']}")

"""Check specific E2E project for errors."""
import json, sys, os
from pathlib import Path

# Find all E2E dirs
projects_dir = Path("F:/Program Files/XEngineer/data/projects")
e2e_dirs = sorted(
    [d for d in projects_dir.iterdir() if d.is_dir() and d.name.startswith("E2E-")],
    key=lambda d: d.stat().st_mtime,
    reverse=True,
)

for proj in e2e_dirs[:3]:
    print(f"\n{'='*60}")
    print(f"Project: {proj.name}")

    # Check novel_analysis
    na_path = proj / "artifacts" / "novel_analysis_v001.json"
    if na_path.exists():
        na = json.loads(na_path.read_text(encoding="utf-8"))
        refs = na.get("source_refs", [])
        print(f"novel_analysis source_refs: {len(refs)}")
        if refs and isinstance(refs[0], dict):
            for r in refs[:5]:
                cid = r.get("chapter_id", "?")
                npara = len(r.get("paragraph_ids", []))
                print(f"  chapter_id={cid} paragraphs={npara}")

    # Check screenplay JSON
    sj_path = proj / "artifacts" / "screenplay_json_v001.json"
    if sj_path.exists():
        sj = json.loads(sj_path.read_text(encoding="utf-8"))
        audit = sj.get("audit_report", {})
        cw = audit.get("continuity_warnings", [])
        print(f"Screenplay: scenes={len(sj.get('scenes', []))}, events={len(sj.get('events', []))}")
        print(f"Continuity warnings: {len(cw)}")
        errors = [w for w in cw if w.get("severity") == "error"]
        warns = [w for w in cw if w.get("severity") != "error"]
        for w in errors[:5]:
            print(f"  ERROR: {w['message'][:150]}")
        for w in warns[:5]:
            print(f"  WARN: {w['message'][:150]}")

    # Check YAML
    yaml_files = list((proj / "artifacts").glob("screenplay_yaml*"))
    print(f"YAML artifacts: {len(yaml_files)}")
    if yaml_files:
        for yf in yaml_files:
            print(f"  {yf.name} ({yf.stat().st_size} bytes)")

    # All artifacts
    all_artifacts = sorted((proj / "artifacts").glob("*"), key=lambda f: f.stat().st_mtime)
    print(f"All artifacts ({len(all_artifacts)}):")
    for a in all_artifacts:
        print(f"  {a.name} ({a.stat().st_size} bytes)")

"""Small-sample real test with DeepSeek provider — 3 micro chapters.

Run from the backend directory (where the app module lives).

Supports two modes:
  --smoke    Smoke the provider (validate structured output shapes)
  --full     Full 3-chapter end-to-end via TestClient
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Ensure the backend package is importable from the project root
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))


def _env(key: str, fallback: str = "") -> str:
    return os.environ.get(key, fallback)


def smoke_deepseek_provider() -> bool:
    """Quick smoke: call each skill standalone and check output shape."""
    from app.ai.providers.deepseek_provider import DeepSeekProvider
    from app.ai.skills.novel_reader import NovelReaderSkill
    from app.ai.skills.story_ontology import StoryOntologySkill
    from app.ai.skills.adaptation_planner import AdaptationPlannerSkill
    from app.ai.skills.screenplay_writer import ScreenplayYamlWriterSkill

    provider = DeepSeekProvider(
        model=_env("XENGINEER_DEEPSEEK_MODEL", "deepseek-v4-flash"),
        api_key=_env("DEEPSEEK_API_KEY"),
        base_url=_env("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        timeout_seconds=float(_env("XENGINEER_LLM_TIMEOUT_SECONDS", "120")),
    )

    chapters = [
        {"id": "chapter_001", "title": "Arrival", "text": "Lin stepped off the train into a town that wasn't on any map. The air smelled of wet stone."},
        {"id": "chapter_002", "title": "The Market", "text": "The market was loud, crowded, and nobody looked Lin in the eye. Something was wrong."},
        {"id": "chapter_003", "title": "The Letter", "text": "A folded letter, yellow with age, sat on the empty bench. It had Lin's name on it."},
    ]

    print("=" * 60)
    print("DeepSeek Provider SMOKE TEST")
    print("=" * 60)

    # 1 — Novel Reader
    print("\n[1/4] novel_reader ...")
    nr = NovelReaderSkill(provider)
    try:
        novel_analysis = nr.run({"chapters": [{"id": c["id"], "title": c["title"], "text": c["text"]} for c in chapters]})
        assert isinstance(novel_analysis, dict), f"Expected dict, got {type(novel_analysis)}"
        assert "chapters" in novel_analysis or "events" in novel_analysis, f"Missing expected keys: {list(novel_analysis.keys())[:5]}"
        print(f"  OK — {len(novel_analysis)} top-level keys: {list(novel_analysis.keys())[:5]}")
    except Exception as exc:
        print(f"  FAIL — {exc}")
        return False

    # 2 — Story Ontology
    print("\n[2/4] story_ontology ...")
    so = StoryOntologySkill(provider)
    try:
        story_assets = so.run(novel_analysis)
        assert isinstance(story_assets, dict), f"Expected dict, got {type(story_assets)}"
        print(f"  OK — keys: {list(story_assets.keys())[:10]}")
    except Exception as exc:
        print(f"  FAIL — {exc}")
        return False

    # 3 — Adaptation Planner
    print("\n[3/4] adaptation_planner ...")
    ap = AdaptationPlannerSkill(provider)
    adapt_config = {"target_format": "web_series", "episode_count": 1, "target_duration_min": 10}
    try:
        adaptation_plan = ap.run({**story_assets, "adaptation_config": adapt_config})
        assert isinstance(adaptation_plan, dict), f"Expected dict, got {type(adaptation_plan)}"
        print(f"  OK — keys: {list(adaptation_plan.keys())[:10]}")
    except Exception as exc:
        print(f"  FAIL — {exc}")
        return False

    # 4 — Screenplay Writer
    print("\n[4/4] screenplay_writer ...")
    sw = ScreenplayYamlWriterSkill(provider)
    try:
        screenplay = sw.run({**story_assets, "adaptation_config": adapt_config, "adaptation_plan": adaptation_plan})
        assert isinstance(screenplay, dict), f"Expected dict, got {type(screenplay)}"
        scenes = screenplay.get("scenes", [])
        print(f"  OK — {len(scenes)} scene(s), keys: {list(screenplay.keys())[:10]}")
    except Exception as exc:
        print(f"  FAIL — {exc}")
        return False

    print("\n" + "=" * 60)
    print("SMOKE PASSED — all 4 DeepSeek skills returned valid JSON")
    print("=" * 60)
    return True


def full_e2e_deepseek() -> bool:
    """Full end-to-end test using FastAPI TestClient + DeepSeek provider."""
    from fastapi.testclient import TestClient
    from app.main import create_app

    print("=" * 60)
    print("DeepSeek FULL END-TO-END TEST (3 mini chapters)")
    print("=" * 60)

    client = TestClient(create_app())

    # Create project
    print("\n[1] Creating project ...")
    r = client.post("/api/projects", json={"title": "DeepSeek Smoke", "logline": "Three chapters, one town.", "target_format": "web_series"})
    assert r.status_code == 200, f"Create project failed: {r.json()}"
    project_id = r.json()["id"]
    print(f"  Created {project_id}")

    # Upload 2 chapters
    print("\n[2] Upload 2 chapters ...")
    r = client.put(f"/api/projects/{project_id}/chapters", json={"chapters": [
        {"title": "Arrival", "text": "Lin stepped off the train. The station was deserted."},
        {"title": "The Market", "text": "Nobody looked at Lin. The stalls were full but silent."},
    ]})
    assert r.status_code == 200

    # Verify rejection (need 3+)
    print("\n[3] Verify generation is rejected with only 2 chapters ...")
    r = client.post(f"/api/projects/{project_id}/generate/screenplay", json={})
    assert r.status_code == 422, f"Expected 422, got {r.status_code}"
    assert r.json()["detail"]["code"] == "cannot-generate"
    print("  OK — correctly rejected")

    # Upload 3 chapters
    print("\n[4] Upload 3rd chapter ...")
    r = client.put(f"/api/projects/{project_id}/chapters", json={"chapters": [
        {"title": "Arrival", "text": "Lin stepped off the train. The station was deserted."},
        {"title": "The Market", "text": "Nobody looked at Lin. The stalls were full but silent."},
        {"title": "The Letter", "text": "A folded letter sat on the bench. It had Lin's name."},
    ]})
    assert r.status_code == 200

    # Trigger generation
    print("\n[5] Triggering DeepSeek generation (this will take ~30-120s) ...")
    r = client.post(f"/api/projects/{project_id}/generate/screenplay", json={})
    assert r.status_code == 200, f"Generate failed: {r.json()}"
    job_id = r.json()["job_id"]
    print(f"  Job: {job_id}")

    # Poll until done
    import time
    print("\n[6] Polling job status ...")
    for i in range(60):
        time.sleep(2.0)
        r = client.get(f"/api/jobs/{job_id}")
        job_data = r.json()
        status = job_data["status"]
        step = job_data["current_step"]
        error = job_data.get("error")
        elapsed = (i + 1) * 2
        print(f"  [{elapsed:3d}s] {status:11s} | step={step} {('error=' + str(error)[:80]) if error else ''}")
        if status in ("succeeded", "failed"):
            break

    if job_data["status"] != "succeeded":
        print(f"\nFAIL — job failed: {job_data.get('error')}")
        return False

    print(f"\n  Job succeeded with {len(job_data['artifact_ids'])} artifacts")

    # Verify artifacts
    print("\n[7] Verifying artifacts ...")
    r = client.get(f"/api/projects/{project_id}/artifacts")
    assert r.status_code == 200
    artifacts = r.json()
    types = {a["type"] for a in artifacts}
    print(f"  Types: {types}")
    expected = {"novel_analysis", "story_bible", "adaptation_plan", "screenplay_json", "screenplay_yaml", "audit_report"}
    missing = expected - types
    if missing:
        print(f"  WARNING — missing artifact types: {missing}")

    # Download YAML
    print("\n[8] Downloading YAML ...")
    r = client.get(f"/api/projects/{project_id}/yaml/download")
    assert r.status_code == 200
    import yaml
    parsed = yaml.safe_load(r.text)
    assert "adaptation_config" in parsed, "YAML missing adaptation_config"
    print(f"  OK — YAML valid, top-level keys: {list(parsed.keys())[:10]}")

    print("\n" + "=" * 60)
    print("E2E PASSED — DeepSeek full pipeline completed successfully")
    print("=" * 60)
    return True


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "smoke"

    # Set env vars from the configure script values
    os.environ.setdefault("XENGINEER_AI_PROVIDER", "deepseek")
    os.environ.setdefault("DEEPSEEK_API_KEY", "sk-ed4fb7302f234b25b2868529d7883b10")
    os.environ.setdefault("XENGINEER_DEEPSEEK_MODEL", "deepseek-v4-flash")
    os.environ.setdefault("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

    # Use a temp data root
    import tempfile
    os.environ.setdefault("XENGINEER_DATA_ROOT", os.path.join(tempfile.gettempdir(), "xengineer-deepseek-test"))

    if mode == "smoke":
        ok = smoke_deepseek_provider()
    elif mode == "full":
        ok = full_e2e_deepseek()
    else:
        print(f"Unknown mode: {mode}. Use 'smoke' or 'full'.")
        sys.exit(1)

    sys.exit(0 if ok else 1)

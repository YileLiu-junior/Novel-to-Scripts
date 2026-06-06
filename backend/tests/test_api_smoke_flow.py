from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest
import yaml
from fastapi.testclient import TestClient

from app.main import create_app
from app.services.artifact_service import ArtifactService

# 数据路径说明：这些 API smoke tests 需要验证 repository-backed persistence，
# 因此通过 XENGINEER_DATA_ROOT 指向 pytest-managed tmp_path，而不是写入仓库内目录。
# These tests exercise the V0+V1 smoke path through the public API while using
# a temp file repository root, proving data survives outside in-memory stubs.


@pytest.fixture
def data_root(tmp_path: Path) -> Path:
    return tmp_path / uuid4().hex


def _client(monkeypatch, data_root: Path) -> TestClient:
    monkeypatch.setenv("XENGINEER_DATA_ROOT", str(data_root))
    return TestClient(create_app())


def _create_project(client: TestClient) -> str:
    response = client.post(
        "/api/projects",
        json={"title": "Smoke Project", "logline": "A structured adaptation demo.", "target_format": "web_series"},
    )
    assert response.status_code == 200
    return response.json()["id"]


def _chapter_payload(count: int) -> dict:
    return {
        "chapters": [
            {"title": f"Chapter {index}", "text": f"Paragraph A {index}\n\nParagraph B {index}"}
            for index in range(1, count + 1)
        ]
    }


def test_api_rejects_two_chapters_then_generates_smoke_artifacts(monkeypatch, data_root) -> None:
    client = _client(monkeypatch, data_root)
    project_id = _create_project(client)

    two_chapters = client.put(f"/api/projects/{project_id}/chapters", json=_chapter_payload(2))
    assert two_chapters.status_code == 200
    assert [chapter["id"] for chapter in two_chapters.json()] == ["chapter_001", "chapter_002"]

    rejected = client.post(f"/api/projects/{project_id}/generate/screenplay", json={})
    assert rejected.status_code == 422
    assert rejected.json()["detail"]["code"] == "cannot-generate"

    three_chapters = client.put(f"/api/projects/{project_id}/chapters", json=_chapter_payload(3))
    assert three_chapters.status_code == 200
    assert [chapter["id"] for chapter in three_chapters.json()] == ["chapter_001", "chapter_002", "chapter_003"]

    generated = client.post(f"/api/projects/{project_id}/generate/screenplay", json={})
    assert generated.status_code == 200
    job_id = generated.json()["job_id"]
    assert generated.json()["status"] == "queued"

    job = client.get(f"/api/jobs/{job_id}")
    assert job.status_code == 200
    job_data = job.json()
    assert job_data["status"] == "succeeded"
    assert job_data["current_step"] == "complete"
    assert job_data["error"] is None
    assert len(job_data["artifact_ids"]) == 7

    artifacts = client.get(f"/api/projects/{project_id}/artifacts")
    assert artifacts.status_code == 200
    artifact_types = {artifact["type"] for artifact in artifacts.json()}
    assert artifact_types == {
        "novel_analysis",
        "story_bible",
        "adaptation_plan",
        "screenplay_json",
        "screenplay_yaml",
        "screenplay_rendered",
        "audit_report",
    }

    latest_yaml = client.get(f"/api/projects/{project_id}/artifacts/screenplay_yaml")
    assert latest_yaml.status_code == 200
    assert latest_yaml.json()["version"] == 1

    download = client.get(f"/api/projects/{project_id}/yaml/download")
    assert download.status_code == 200
    parsed = yaml.safe_load(download.text)
    assert parsed["adaptation_config"]["target_format"] == "web_series"
    assert "adaptation_plan" in parsed

    restarted_client = _client(monkeypatch, data_root)
    persisted_project = restarted_client.get(f"/api/projects/{project_id}")
    persisted_chapters = restarted_client.get(f"/api/projects/{project_id}/chapters")
    persisted_job = restarted_client.get(f"/api/jobs/{job_id}")
    assert persisted_project.status_code == 200
    assert persisted_chapters.status_code == 200
    assert len(persisted_chapters.json()) == 3
    assert persisted_job.json()["status"] == "succeeded"


def test_artifact_versions_increment(monkeypatch, data_root) -> None:
    monkeypatch.setenv("XENGINEER_DATA_ROOT", str(data_root))
    service = ArtifactService()

    first = service.save_artifact("project_versions", "screenplay_yaml", "a: 1\n")
    second = service.save_artifact("project_versions", "screenplay_yaml", "a: 2\n")

    assert first.version == 1
    assert second.version == 2
    assert service.latest_for_project("project_versions", "screenplay_yaml").data == "a: 2\n"


def test_yaml_download_returns_clear_404_before_generation(monkeypatch, data_root) -> None:
    client = _client(monkeypatch, data_root)
    project_id = _create_project(client)

    response = client.get(f"/api/projects/{project_id}/yaml/download")

    assert response.status_code == 404
    assert response.json()["detail"] == "No screenplay_yaml artifact exists for this project yet."

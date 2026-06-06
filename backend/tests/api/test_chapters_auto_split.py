from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import create_app


def test_auto_split_response_shape_stays_stable(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("XENGINEER_DATA_ROOT", str(tmp_path))
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"title": "拆章测试"}).json()

    response = client.post(
        f"/api/projects/{project['id']}/chapters/auto-split",
        json={
            "text": (
                "声明:仅供预览交流。\n\n"
                "第一章 雨夜归来\n正文一。\n\n"
                "第二章 旧案重启\n正文二。\n\n"
                "第三章 钟声之后\n正文三。"
            )
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert set(payload.keys()) == {"chapters", "chapter_count", "mode_used"}
    assert payload["chapter_count"] == 3
    assert payload["chapters"][0]["title"] == "第一章 雨夜归来"


def test_ai_auto_split_keeps_heading_body_groups(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("XENGINEER_DATA_ROOT", str(tmp_path))
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"title": "AI 拆章测试"}).json()

    response = client.post(
        f"/api/projects/{project['id']}/chapters/auto-split",
        json={
            "mode": "ai",
            "text": (
                "声明:仅供预览交流。\n\n"
                "第一章 雨夜归来\n正文一。\n\n"
                "第二章 旧案重启\n正文二。\n\n"
                "第三章 钟声之后\n正文三。"
            ),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["mode_used"] == "ai"
    assert [chapter["title"] for chapter in payload["chapters"]] == ["第一章 雨夜归来", "第二章 旧案重启", "第三章 钟声之后"]
    assert "正文一" in payload["chapters"][0]["text"]

"""Run the live frontend-backend acceptance path for the XEngineer V0+V1 API.

This script is intentionally stdlib-only so frontend developers can verify the
backend integration contract without installing extra test tooling. It creates a
throwaway project, imports three chapters, runs generation, checks artifacts,
downloads exports, validates YAML, and verifies frontend editable data storage.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass
from typing import Any
from urllib import error, parse, request


DEFAULT_BASE_URL = "http://localhost:8000"


class ApiError(RuntimeError):
    """HTTP failure with enough context for a frontend developer to debug."""

    def __init__(self, method: str, path: str, status: int | None, detail: str) -> None:
        super().__init__(f"{method} {path} failed: {status or 'network'} {detail}")
        self.method = method
        self.path = path
        self.status = status
        self.detail = detail


@dataclass
class Downloaded:
    """Binary response metadata for download endpoints."""

    content: bytes
    content_type: str
    disposition: str


class AcceptanceRunner:
    """Orchestrates the same backend path the Streamlit frontend must consume."""

    def __init__(self, base_url: str, timeout_seconds: float, poll_interval: float, title: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.poll_interval = poll_interval
        self.title = title
        self.passed: list[str] = []
        self.project_id: str | None = None
        self.job_id: str | None = None
        self.yaml_text = ""

    def run(self) -> None:
        self.health()
        self.rejects_two_chapters()
        self.create_project()
        self.import_chapters()
        self.generate_and_poll()
        screenplay = self.verify_artifacts()
        self.verify_rendered_and_exports()
        self.verify_frontend_data(screenplay)

    def pass_step(self, name: str) -> None:
        self.passed.append(name)
        print(f"PASS {name}")

    def fail(self, name: str, exc: BaseException) -> None:
        print(f"FAIL {name}: {exc}")
        raise SystemExit(1) from exc

    def url(self, path: str, query: dict[str, str] | None = None) -> str:
        target = f"{self.base_url}{path}"
        if query:
            target = f"{target}?{parse.urlencode(query)}"
        return target

    def request_json(self, method: str, path: str, payload: dict[str, Any] | None = None) -> Any:
        body = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers = {"Accept": "application/json"}
        if body is not None:
            headers["Content-Type"] = "application/json; charset=utf-8"
        req = request.Request(self.url(path), data=body, headers=headers, method=method)
        try:
            with request.urlopen(req, timeout=30) as response:
                raw = response.read()
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise ApiError(method, path, exc.code, detail) from exc
        except error.URLError as exc:
            raise ApiError(method, path, None, str(exc)) from exc
        if not raw:
            return None
        try:
            return json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise ApiError(method, path, None, f"invalid JSON: {exc}") from exc

    def download(self, path: str, query: dict[str, str] | None = None) -> Downloaded:
        req = request.Request(self.url(path, query), headers={"Accept": "*/*"}, method="GET")
        try:
            with request.urlopen(req, timeout=30) as response:
                return Downloaded(
                    content=response.read(),
                    content_type=response.headers.get("Content-Type", ""),
                    disposition=response.headers.get("Content-Disposition", ""),
                )
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise ApiError("GET", path, exc.code, detail) from exc
        except error.URLError as exc:
            raise ApiError("GET", path, None, str(exc)) from exc

    def assert_true(self, condition: bool, message: str) -> None:
        if not condition:
            raise AssertionError(message)

    def health(self) -> None:
        try:
            data = self.request_json("GET", "/api/health")
            self.assert_true(isinstance(data, dict), "health response must be an object")
            self.assert_true(data.get("status") == "ok", "health.status must be ok")
            self.pass_step("health")
        except BaseException as exc:
            self.fail("health", exc)

    def create_project(self) -> None:
        try:
            project = self.create_project_payload(self.title)
            self.project_id = project.get("id")
            self.assert_true(bool(self.project_id), "project response must include id")
            fetched = self.request_json("GET", f"/api/projects/{self.project_id}")
            self.assert_true(fetched.get("id") == self.project_id, "GET project must return created project")
            self.assert_true(fetched.get("target_format") == "web_series", "project target_format must persist")
            self.pass_step("create_project")
        except BaseException as exc:
            self.fail("create_project", exc)

    def create_project_payload(self, title: str) -> dict[str, Any]:
        """Create a backend project with the same shape the frontend sends."""

        return self.request_json(
            "POST",
            "/api/projects",
            {
                "title": title,
                "logline": "Frontend backend acceptance check",
                "target_format": "web_series",
            },
        )

    def rejects_two_chapters(self) -> None:
        try:
            project = self.create_project_payload(f"{self.title}-rejects-two-chapters")
            project_id = project.get("id")
            self.assert_true(bool(project_id), "project response must include id")
            saved = self.request_json(
                "PUT",
                f"/api/projects/{project_id}/chapters",
                {
                    "chapters": [
                        {"title": "Chapter 1", "text": "Paragraph A 1\n\nParagraph B 1"},
                        {"title": "Chapter 2", "text": "Paragraph A 2\n\nParagraph B 2"},
                    ]
                },
            )
            self.assert_true(len(saved) == 2, "two chapter setup must save exactly 2 chapters")
            try:
                self.request_json("POST", f"/api/projects/{project_id}/generate/screenplay", {})
            except ApiError as exc:
                self.assert_true(exc.status == 422, "two chapters must be rejected with HTTP 422")
                self.assert_true("cannot-generate" in exc.detail, "422 response must expose cannot-generate")
                self.pass_step("rejects_two_chapters")
                return
            raise AssertionError("generation with two chapters unexpectedly succeeded")
        except BaseException as exc:
            self.fail("rejects_two_chapters", exc)

    def import_chapters(self) -> None:
        try:
            project_id = self.required_project_id()
            text = acceptance_novel_text()
            split = self.request_json(
                "POST",
                f"/api/projects/{project_id}/chapters/auto-split",
                {"text": text, "mode": "auto"},
            )
            self.assert_true(split.get("chapter_count", 0) >= 3, "auto-split must return at least 3 chapters")
            chapters = self.request_json("GET", f"/api/projects/{project_id}/chapters")
            self.assert_true(isinstance(chapters, list), "chapters response must be a list")
            self.assert_true(len(chapters) >= 3, "saved chapters must contain at least 3 chapters")
            first = chapters[0]
            self.assert_true(str(first.get("id", "")).startswith("chapter_"), "chapter id must start with chapter_")
            paragraphs = first.get("paragraphs") or []
            self.assert_true(bool(paragraphs), "first chapter must contain paragraphs")
            self.assert_true(str(paragraphs[0].get("id", "")).startswith("p_"), "paragraph id must start with p_")
            self.pass_step("chapter_intake")
        except BaseException as exc:
            self.fail("chapter_intake", exc)

    def generate_and_poll(self) -> None:
        try:
            project_id = self.required_project_id()
            response = self.request_json(
                "POST",
                f"/api/projects/{project_id}/generate/screenplay",
                {
                    "adaptation_config": {
                        "target_format": "web_series",
                        "fidelity_level": "high",
                        "preserve_priorities": ["relationship_arc", "foreshadowing"],
                        "dialogue_style": "restrained_with_subtext",
                        "adaptation_evidence_mode": "enabled",
                    }
                },
            )
            self.job_id = response.get("job_id")
            self.assert_true(bool(self.job_id), "generate response must include job_id")
            deadline = time.time() + self.timeout_seconds
            last_job: dict[str, Any] = {}
            while time.time() < deadline:
                last_job = self.request_json("GET", f"/api/jobs/{self.job_id}")
                status = last_job.get("status")
                current_step = last_job.get("current_step")
                print(f"INFO job status={status} current_step={current_step}")
                if status == "succeeded":
                    artifact_ids = last_job.get("artifact_ids") or []
                    self.assert_true(bool(artifact_ids), "succeeded job must expose artifact_ids")
                    self.pass_step("generate_job")
                    return
                if status == "failed":
                    raise AssertionError(f"job failed: {last_job.get('error')}")
                time.sleep(self.poll_interval)
            raise TimeoutError(f"job did not finish within {self.timeout_seconds} seconds: {last_job}")
        except BaseException as exc:
            self.fail("generate_job", exc)

    def verify_artifacts(self) -> dict[str, Any]:
        try:
            project_id = self.required_project_id()
            artifacts = self.request_json("GET", f"/api/projects/{project_id}/artifacts")
            artifact_types = {item.get("type") for item in artifacts if isinstance(item, dict)}
            required = {
                "novel_analysis",
                "story_bible",
                "adaptation_plan",
                "screenplay_json",
                "screenplay_yaml",
                "audit_report",
                "screenplay_rendered",
            }
            missing = sorted(required - artifact_types)
            self.assert_true(not missing, f"missing required artifacts: {missing}")

            screenplay_artifact = self.request_json("GET", f"/api/projects/{project_id}/artifacts/screenplay_json")
            screenplay = screenplay_artifact.get("data")
            self.assert_true(isinstance(screenplay, dict), "screenplay_json.data must be an object")
            self.assert_true(bool(screenplay.get("scenes")), "screenplay_json.data.scenes must be non-empty")
            self.assert_true(isinstance(screenplay.get("adaptation_config"), dict), "adaptation_config must exist")
            self.assert_true(isinstance(screenplay.get("adaptation_plan"), dict), "adaptation_plan must exist")

            yaml_artifact = self.request_json("GET", f"/api/projects/{project_id}/artifacts/screenplay_yaml")
            self.yaml_text = yaml_artifact.get("data") or ""
            self.assert_true(isinstance(self.yaml_text, str) and bool(self.yaml_text), "screenplay_yaml.data must be text")

            audit = self.request_json("GET", f"/api/projects/{project_id}/artifacts/audit_report")
            self.assert_true("data" in audit, "audit_report artifact must include data")
            rendered = self.request_json("GET", f"/api/projects/{project_id}/artifacts/screenplay_rendered")
            self.assert_true("data" in rendered, "screenplay_rendered artifact must include data")
            self.pass_step("artifacts")
            return screenplay
        except BaseException as exc:
            self.fail("artifacts", exc)
            raise

    def verify_rendered_and_exports(self) -> None:
        try:
            project_id = self.required_project_id()
            for format_name in ("markdown", "text"):
                preview = self.request_json(
                    "GET",
                    f"/api/projects/{project_id}/screenplay/rendered?format={format_name}",
                )
                self.assert_true(bool(preview.get("content")), f"{format_name} preview content must be non-empty")
                rendered_file = self.download(
                    f"/api/projects/{project_id}/screenplay/rendered/download",
                    {"format": format_name},
                )
                self.assert_true(bool(rendered_file.content), f"{format_name} download must be non-empty")

            yaml_file = self.download(f"/api/projects/{project_id}/yaml/download")
            self.assert_true(bool(yaml_file.content), "YAML download must be non-empty")
            validation = self.request_json(
                "POST",
                f"/api/projects/{project_id}/yaml/validate",
                {"yaml_text": self.yaml_text or yaml_file.content.decode("utf-8", errors="replace")},
            )
            self.assert_true(isinstance(validation.get("findings"), list), "YAML validation must return findings list")
            schema = self.request_json("GET", f"/api/projects/{project_id}/schema/download")
            self.assert_true(bool(schema.get("schema_text")), "schema download must include schema_text")
            self.pass_step("render_export_schema")
        except BaseException as exc:
            self.fail("render_export_schema", exc)

    def verify_frontend_data(self, screenplay: dict[str, Any]) -> None:
        try:
            project_id = self.required_project_id()
            initialized = self.request_json("POST", f"/api/projects/{project_id}/frontend-data/init", {"force": True})
            required_keys = [
                "characters",
                "character_relations",
                "scenes",
                "scene_relations",
                "plots",
                "causal_relations",
                "meta",
            ]
            for key in required_keys:
                self.assert_true(key in initialized, f"frontend-data init must include {key}")
            self.assert_true(isinstance(initialized["characters"], list), "characters must be a list")
            self.assert_true(isinstance(initialized["scenes"], list), "scenes must be a list")

            fetched = self.request_json("GET", f"/api/projects/{project_id}/frontend-data")
            for key in required_keys:
                self.assert_true(key in fetched, f"frontend-data get must include {key}")

            saved_payload = {
                "characters": fetched.get("characters", []),
                "character_relations": fetched.get("character_relations", []),
                "scenes": fetched.get("scenes", []),
                "scene_relations": fetched.get("scene_relations", []),
                "plots": fetched.get("plots", []),
                "causal_relations": fetched.get("causal_relations", []),
            }
            saved = self.request_json("PUT", f"/api/projects/{project_id}/frontend-data", saved_payload)
            self.assert_true(isinstance(saved.get("meta"), dict), "frontend-data put must return meta")
            self.assert_true(saved.get("meta", {}).get("updated_at"), "frontend-data meta must include updated_at")
            self.assert_true(
                len(saved.get("scenes", [])) == len(saved_payload["scenes"]),
                "frontend-data put must preserve scenes count",
            )
            self.assert_true(bool(screenplay.get("scenes")), "screenplay input sanity check must have scenes")
            self.pass_step("frontend_data")
        except BaseException as exc:
            self.fail("frontend_data", exc)

    def required_project_id(self) -> str:
        if not self.project_id:
            raise AssertionError("project_id is not available")
        return self.project_id

    def summary(self) -> None:
        print("\nACCEPTANCE SUMMARY")
        print(f"passed: {len(self.passed)}")
        print("failed: 0")
        print(f"project_id: {self.project_id or ''}")
        print(f"job_id: {self.job_id or ''}")


def acceptance_novel_text() -> str:
    """Small three-chapter source text with clear chapter markers for intake."""

    return """第一章 雨夜旧案
林晚在雨夜回到旧巷，发现周砚守在废弃照相馆门口。门缝里透出一线灯光，像十年前那场失踪案留下的伤口。
她不愿承认自己一直在等一个解释，只把伞柄攥得更紧。周砚说，旧相机里还有最后一卷胶片。

第二章 暗房证词
暗房里漂浮着药水味。照片逐渐显影，林晚看见父亲失踪前最后一次出现的背影。
周砚承认当年隐瞒了一段证词，因为证词会把林晚也拖进危险。两人的信任在红光里摇晃。

第三章 天台重逢
清晨，林晚带着照片登上天台。真正的证人终于出现，却只愿把真相交给她一个人。
周砚没有替她做决定，只站在楼梯口等她回头。林晚明白，这次她要亲手把旧案重新打开。
"""


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run XEngineer frontend-backend acceptance checks.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="FastAPI backend base URL.")
    parser.add_argument("--timeout-seconds", type=float, default=180.0, help="Maximum time to wait for generation.")
    parser.add_argument("--poll-interval", type=float, default=1.5, help="Job polling interval in seconds.")
    parser.add_argument(
        "--project-title",
        default=f"frontend-acceptance-{time.strftime('%Y%m%d-%H%M%S')}",
        help="Throwaway project title.",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    runner = AcceptanceRunner(
        base_url=args.base_url,
        timeout_seconds=args.timeout_seconds,
        poll_interval=args.poll_interval,
        title=args.project_title,
    )
    runner.run()
    runner.summary()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

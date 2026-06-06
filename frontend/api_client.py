"""
api_client.py
统一封装 Streamlit 前端访问 XEngineer 后端的 HTTP 调用。

该模块只负责请求、下载和错误翻译，不保存页面状态，也不把 API path
散落到各个 view 组件里。
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any
from urllib import error, parse, request


DEFAULT_BASE_URL = "http://localhost:8000"


class ApiClientError(Exception):
    """面向页面展示的后端调用错误。"""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


@dataclass(frozen=True)
class DownloadedFile:
    """下载接口的返回结构，保留文件名、MIME 和原始 bytes。"""

    content: bytes
    filename: str
    media_type: str


def get_base_url() -> str:
    """读取可配置 Base URL，默认连接本地 FastAPI 后端。"""
    return os.getenv("XENGINEER_API_BASE_URL") or os.getenv("STREAMLIT_API_BASE_URL") or DEFAULT_BASE_URL


def _build_url(path: str, query: dict[str, str] | None = None) -> str:
    base = get_base_url().rstrip("/")
    url = f"{base}{path}"
    if query:
        url = f"{url}?{parse.urlencode(query)}"
    return url


def _extract_filename(headers: Any, fallback: str) -> str:
    disposition = headers.get("Content-Disposition", "") if headers else ""
    marker = "filename="
    if marker not in disposition:
        return fallback
    return disposition.split(marker, 1)[1].strip().strip('"') or fallback


def _translate_error(status_code: int | None, detail: Any) -> str:
    """把后端/网络错误翻译成用户可理解的中文提示。"""
    if status_code is None:
        return "无法连接后端服务，请确认 FastAPI 已启动并检查 Base URL。"

    message = detail
    if isinstance(detail, dict):
        message = detail.get("message") or detail.get("detail") or detail.get("code") or detail
    if isinstance(message, list):
        message = "；".join(str(item) for item in message)
    if not message:
        message = f"请求失败（HTTP {status_code}）。"

    if status_code == 400:
        return f"请求参数不正确：{message}"
    if status_code == 404:
        return f"资源不存在或尚未生成：{message}"
    if status_code == 422:
        return f"当前数据还不能执行该操作：{message}"
    return f"后端请求失败（HTTP {status_code}）：{message}"


def _request_json(method: str, path: str, payload: dict[str, Any] | None = None) -> Any:
    body = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {"Accept": "application/json"}
    if body is not None:
        headers["Content-Type"] = "application/json; charset=utf-8"

    req = request.Request(_build_url(path), data=body, headers=headers, method=method)
    try:
        with request.urlopen(req, timeout=20) as response:
            raw = response.read()
    except error.HTTPError as exc:
        raw = exc.read()
        try:
            detail = json.loads(raw.decode("utf-8")).get("detail")
        except Exception:
            detail = raw.decode("utf-8", errors="ignore")
        raise ApiClientError(_translate_error(exc.code, detail), exc.code) from exc
    except error.URLError as exc:
        raise ApiClientError(_translate_error(None, str(exc))) from exc
    except TimeoutError as exc:
        raise ApiClientError("连接后端超时，请稍后重试。") from exc

    if not raw:
        return None
    try:
        return json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise ApiClientError("后端返回了无法解析的 JSON。") from exc


def _download(path: str, query: dict[str, str] | None, fallback_name: str) -> DownloadedFile:
    req = request.Request(_build_url(path, query), headers={"Accept": "*/*"}, method="GET")
    try:
        with request.urlopen(req, timeout=20) as response:
            content = response.read()
            filename = _extract_filename(response.headers, fallback_name)
            media_type = response.headers.get("Content-Type", "application/octet-stream")
            return DownloadedFile(content=content, filename=filename, media_type=media_type)
    except error.HTTPError as exc:
        raw = exc.read()
        try:
            detail = json.loads(raw.decode("utf-8")).get("detail")
        except Exception:
            detail = raw.decode("utf-8", errors="ignore")
        raise ApiClientError(_translate_error(exc.code, detail), exc.code) from exc
    except error.URLError as exc:
        raise ApiClientError(_translate_error(None, str(exc))) from exc


def create_project(title: str, logline: str | None = None, target_format: str = "web_series") -> dict[str, Any]:
    return _request_json("POST", "/api/projects", {"title": title, "logline": logline, "target_format": target_format})


def get_project(project_id: str) -> dict[str, Any]:
    return _request_json("GET", f"/api/projects/{project_id}")


def replace_chapters(project_id: str, chapters: list[dict[str, str]]) -> list[dict[str, Any]]:
    return _request_json("PUT", f"/api/projects/{project_id}/chapters", {"chapters": chapters})


def list_chapters(project_id: str) -> list[dict[str, Any]]:
    return _request_json("GET", f"/api/projects/{project_id}/chapters")


def auto_split_chapters(project_id: str, text: str, mode: str = "auto") -> dict[str, Any]:
    return _request_json("POST", f"/api/projects/{project_id}/chapters/auto-split", {"text": text, "mode": mode})


def generate_screenplay(project_id: str, adaptation_config: dict[str, Any]) -> dict[str, Any]:
    return _request_json("POST", f"/api/projects/{project_id}/generate/screenplay", {"adaptation_config": adaptation_config})


def get_job(job_id: str) -> dict[str, Any]:
    return _request_json("GET", f"/api/jobs/{job_id}")


def list_artifacts(project_id: str) -> list[dict[str, Any]]:
    return _request_json("GET", f"/api/projects/{project_id}/artifacts")


def get_artifact(project_id: str, artifact_type: str) -> dict[str, Any]:
    return _request_json("GET", f"/api/projects/{project_id}/artifacts/{artifact_type}")


def validate_yaml(project_id: str, yaml_text: str) -> dict[str, Any]:
    return _request_json("POST", f"/api/projects/{project_id}/yaml/validate", {"yaml_text": yaml_text})


def get_rendered(project_id: str, format_name: str = "markdown") -> dict[str, Any]:
    return _request_json("GET", f"/api/projects/{project_id}/screenplay/rendered?format={format_name}")


def download_yaml(project_id: str) -> DownloadedFile:
    return _download(f"/api/projects/{project_id}/yaml/download", None, "demo_screenplay.yaml")


def download_rendered(project_id: str, format_name: str) -> DownloadedFile:
    suffix = "md" if format_name == "markdown" else "txt"
    return _download(
        f"/api/projects/{project_id}/screenplay/rendered/download",
        {"format": format_name},
        f"screenplay.{suffix}",
    )


def download_schema(project_id: str) -> dict[str, Any]:
    return _request_json("GET", f"/api/projects/{project_id}/schema/download")

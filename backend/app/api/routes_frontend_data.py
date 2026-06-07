from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.repositories.file_store import default_data_root, ensure_directory, read_json, write_json_atomic
from app.services.artifact_service import ArtifactService
from app.services.project_service import ProjectService

router = APIRouter()

# frontend_data 子目录名
_FRONTEND_DATA_DIR = "frontend_data"

# 7 个数据文件名
_DATA_FILES = [
    "characters",
    "character_relations",
    "scenes",
    "scene_relations",
    "plots",
    "causal_relations",
    "meta",
]


def _frontend_data_dir(project_id: str) -> Path:
    """获取项目的 frontend_data 目录路径。"""
    return default_data_root() / "projects" / project_id / _FRONTEND_DATA_DIR


def _is_initialized(project_id: str) -> bool:
    """检查 frontend_data 是否已初始化。"""
    fd = _frontend_data_dir(project_id)
    return fd.exists() and (fd / "meta.json").exists()


def _read_file(project_id: str, name: str) -> Any:
    """读取单个 frontend_data JSON 文件。"""
    path = _frontend_data_dir(project_id) / f"{name}.json"
    return read_json(path, {"items": []})


def _write_file(project_id: str, name: str, data: Any) -> None:
    """写入单个 frontend_data JSON 文件。"""
    path = _frontend_data_dir(project_id) / f"{name}.json"
    write_json_atomic(path, data)


class InitRequest(BaseModel):
    force: bool = False


class FrontendDataResponse(BaseModel):
    characters: list = []
    character_relations: list = []
    scenes: list = []
    scene_relations: list = []
    plots: list = []
    causal_relations: list = []
    meta: dict = {}


@router.post("/{project_id}/frontend-data/init", response_model=FrontendDataResponse)
def init_frontend_data(project_id: str, body: InitRequest = InitRequest()) -> FrontendDataResponse:
    """初始化前端专用数据：从 screenplay_json 提取并转换为前端可编辑格式。"""
    if ProjectService().get_project(project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    fd = _frontend_data_dir(project_id)

    # 如果已初始化且不强制覆盖，直接返回已有数据
    if _is_initialized(project_id) and not body.force:
        return _get_all_data(project_id)

    # 读取最新 screenplay_json
    artifact = ArtifactService().get_for_project(project_id, "screenplay_json")
    if artifact is None:
        raise HTTPException(status_code=404, detail="screenplay_json artifact not found. Please generate first.")

    sp = artifact.data if isinstance(artifact.data, dict) else {}

    # 转换 characters
    story_bible = sp.get("story_bible", {})
    raw_chars = story_bible.get("characters", [])
    characters = []
    for c in raw_chars:
        characters.append({
            "id": c.get("id", ""),
            "name": c.get("name", ""),
            "aliases": c.get("aliases", []),
            "narrative_role": c.get("narrative_role", ""),
            "voice_profile": c.get("voice_profile", {}),
            "source_refs": c.get("source_refs", []),
            "description": c.get("description", ""),
        })

    # 转换 character_relations
    raw_rels = story_bible.get("relationship_edges", [])
    char_rels = []
    for i, r in enumerate(raw_rels):
        char_rels.append({
            "id": r.get("id", f"char_rel_{i+1:03d}"),
            "from": r.get("from", ""),
            "to": r.get("to", ""),
            "relation": r.get("relation", r.get("type", "")),
            "current_state": r.get("current_state", ""),
            "description": r.get("description", ""),
        })

    # 转换 scenes
    raw_scenes = sp.get("scenes", [])
    scenes = []
    for s in raw_scenes:
        heading = s.get("scene_heading", {})
        loc = s.get("location", {})
        scenes.append({
            "id": s.get("id", ""),
            "title": s.get("title", ""),
            "sequence": heading.get("sequence", 0),
            "location": loc.get("name", heading.get("location", "")),
            "time": loc.get("time", heading.get("time_of_day", "")),
            "interior_exterior": loc.get("interior_exterior", heading.get("interior_exterior", "")),
            "heading_text": heading.get("text", ""),
            "characters": s.get("characters", []),
            "dramatic_purpose": s.get("dramatic_purpose", []),
            "related_events": s.get("related_events", []),
            "action": s.get("action", []),
            "dialogue": s.get("dialogue", []),
            "content_blocks": s.get("content_blocks", []),
            "source_refs": s.get("source_refs", []),
        })

    # 转换 scene_relations (from adaptation_plan.scene_plan)
    adapt_plan = sp.get("adaptation_plan", {})
    raw_scene_plan = adapt_plan.get("scene_plan", [])
    scene_rels = []
    for i, p in enumerate(raw_scene_plan):
        scene_rels.append({
            "id": p.get("id", f"scene_rel_{i+1:03d}"),
            "from": p.get("scene_id", ""),
            "to": "",
            "relation": "planning",
            "description": p.get("purpose", ""),
        })

    # 转换 plots (from events)
    raw_events = sp.get("events", [])
    plots = []
    for e in raw_events:
        plots.append({
            "id": e.get("id", ""),
            "title": e.get("title", ""),
            "description": e.get("summary", e.get("description", "")),
            "characters": e.get("characters", []),
            "source_refs": e.get("source_refs", []),
            "type": e.get("type", ""),
            "importance": e.get("importance", ""),
        })

    # 转换 causal_relations
    causal = sp.get("causal_graph", {})
    raw_edges = causal.get("edges", [])
    causal_rels = []
    for i, edge in enumerate(raw_edges):
        causal_rels.append({
            "id": edge.get("id", f"cause_{i+1:03d}"),
            "from": edge.get("from", ""),
            "to": edge.get("to", ""),
            "relation": edge.get("relation", ""),
            "description": edge.get("reason", edge.get("evidence", "")),
        })

    # meta
    now = datetime.now().isoformat()
    meta = {
        "project_id": project_id,
        "source_artifact": "screenplay_json",
        "initialized_at": now,
        "updated_at": now,
        "version": 1,
    }

    # 写入文件
    ensure_directory(fd)
    _write_file(project_id, "characters", {"items": characters})
    _write_file(project_id, "character_relations", {"items": char_rels})
    _write_file(project_id, "scenes", {"items": scenes})
    _write_file(project_id, "scene_relations", {"items": scene_rels})
    _write_file(project_id, "plots", {"items": plots})
    _write_file(project_id, "causal_relations", {"items": causal_rels})
    _write_file(project_id, "meta", meta)

    return FrontendDataResponse(
        characters=characters,
        character_relations=char_rels,
        scenes=scenes,
        scene_relations=scene_rels,
        plots=plots,
        causal_relations=causal_rels,
        meta=meta,
    )


def _get_all_data(project_id: str) -> FrontendDataResponse:
    """读取所有 frontend_data 文件。"""
    chars = _read_file(project_id, "characters")
    char_rels = _read_file(project_id, "character_relations")
    scenes = _read_file(project_id, "scenes")
    scene_rels = _read_file(project_id, "scene_relations")
    plots = _read_file(project_id, "plots")
    causal_rels = _read_file(project_id, "causal_relations")
    meta = _read_file(project_id, "meta")

    return FrontendDataResponse(
        characters=chars.get("items", []),
        character_relations=char_rels.get("items", []),
        scenes=scenes.get("items", []),
        scene_relations=scene_rels.get("items", []),
        plots=plots.get("items", []),
        causal_relations=causal_rels.get("items", []),
        meta=meta,
    )


@router.get("/{project_id}/frontend-data", response_model=FrontendDataResponse)
def get_frontend_data(project_id: str) -> FrontendDataResponse:
    """获取前端专用数据。"""
    if ProjectService().get_project(project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    if not _is_initialized(project_id):
        raise HTTPException(status_code=404, detail="frontend_data not initialized. Please call init first.")
    return _get_all_data(project_id)


class SaveFrontendDataRequest(BaseModel):
    characters: list = []
    character_relations: list = []
    scenes: list = []
    scene_relations: list = []
    plots: list = []
    causal_relations: list = []


@router.put("/{project_id}/frontend-data", response_model=FrontendDataResponse)
def save_frontend_data(project_id: str, body: SaveFrontendDataRequest) -> FrontendDataResponse:
    """保存前端专用数据。"""
    if ProjectService().get_project(project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    fd = _frontend_data_dir(project_id)
    ensure_directory(fd)

    _write_file(project_id, "characters", {"items": body.characters})
    _write_file(project_id, "character_relations", {"items": body.character_relations})
    _write_file(project_id, "scenes", {"items": body.scenes})
    _write_file(project_id, "scene_relations", {"items": body.scene_relations})
    _write_file(project_id, "plots", {"items": body.plots})
    _write_file(project_id, "causal_relations", {"items": body.causal_relations})

    # 更新 meta
    meta = _read_file(project_id, "meta")
    if not meta or not isinstance(meta, dict):
        meta = {"project_id": project_id}
    meta["updated_at"] = datetime.now().isoformat()
    meta["version"] = meta.get("version", 0) + 1
    _write_file(project_id, "meta", meta)

    return _get_all_data(project_id)

"""
storage.py
负责本地 JSON 数据的读写、项目的增删改查。
所有项目数据保存在 data/projects.json 中。
"""

import json
import os
import uuid
from datetime import datetime

# 数据文件路径（指向 backend/data 目录，与后端数据根目录一致）
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "backend", "data")
DATA_FILE = os.path.join(DATA_DIR, "projects.json")


def _ensure_data_dir():
    """
    确保 data 目录存在。
    """
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)


def _load_all() -> dict:
    """
    读取整个 projects.json 内容。
    返回字典格式，包含 projects 列表。
    如果文件不存在或内容损坏，返回初始空数据结构。
    """
    _ensure_data_dir()
    if not os.path.exists(DATA_FILE):
        return {"projects": []}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return {"projects": []}
        if "projects" not in data:
            data["projects"] = []
        return data
    except (json.JSONDecodeError, OSError):
        return {"projects": []}


def _save_all(data: dict):
    """
    将整个数据字典写入 projects.json。
    会自动创建目录和文件。
    """
    _ensure_data_dir()
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _migrate_project(project: dict) -> dict:
    """
    兼容旧数据迁移：
    1. 如果项目没有 acts 字段，但 scenes 中元素包含 title/summary，
       则认为旧 scenes 是旧版场次，迁移到 acts。
    2. 新的 scenes 初始化为空数组。
    3. 确保所有字段存在。
    """
    # 确保 scenes 存在
    if "scenes" not in project:
        project["scenes"] = []

    # 确保 acts 存在
    if "acts" not in project:
        # 检查旧 scenes 是否实际是场次数据（包含 title 或 summary）
        old_scenes = project.get("scenes", [])
        if old_scenes and any(
            isinstance(s, dict) and (s.get("title") or s.get("summary"))
            for s in old_scenes
        ):
            # 迁移旧 scenes 到 acts
            project["acts"] = []
            for old in old_scenes:
                if isinstance(old, dict):
                    project["acts"].append({
                        "id": old.get("id", str(uuid.uuid4())),
                        "title": old.get("title", ""),
                        "scene_id": "",
                        "time": old.get("time", ""),
                        "summary": old.get("summary", ""),
                        "content": "",
                    })
            # 清空 scenes，让它变成真正的场景数组
            project["scenes"] = []
        else:
            project["acts"] = []

    # 确保 characters 存在
    if "characters" not in project:
        project["characters"] = []

    # 确保 original_text 存在
    if "original_text" not in project:
        project["original_text"] = ""

    # 后端联调字段：本地项目只负责记住后端 project/job/artifact 的当前快照。
    backend_defaults = {
        "backend_project_id": None,
        "backend_chapters": [],
        "backend_job_id": None,
        "backend_job_status": "idle",
        "backend_current_step": None,
        "backend_error": None,
        "backend_artifacts": [],
        "screenplay_data": {},
        "screenplay_yaml": "",
        "rendered_markdown": "",
    }
    for key, value in backend_defaults.items():
        if key not in project:
            project[key] = value

    return project


def get_all_projects() -> list:
    """
    获取所有项目列表。
    返回 projects 数组，并自动迁移旧数据。
    """
    data = _load_all()
    projects = data.get("projects", [])
    # 自动迁移每个项目
    for p in projects:
        _migrate_project(p)
    return projects


def get_project_by_id(project_id: str) -> dict | None:
    """
    根据项目 id 获取单个项目详情。
    如果找不到，返回 None。
    会自动迁移旧数据。
    """
    projects = get_all_projects()
    for project in projects:
        if project.get("id") == project_id:
            return project
    return None


def create_project(name: str, description: str = "") -> dict:
    """
    创建新项目。
    自动生成 uuid、创建时间和更新时间。
    预初始化所有前端需要的空数据结构，避免页面白屏或字段缺失。
    返回创建后的项目字典。
    """
    now = datetime.now().isoformat()
    new_project = {
        "id": str(uuid.uuid4()),
        "name": name,
        "description": description,
        "created_at": now,
        "updated_at": now,
        "original_text": "",
        "characters": [],
        "scenes": [],
        "acts": [],
        # 后端联调字段：预初始化空值，避免页面访问时报 KeyError
        "backend_project_id": None,
        "backend_chapters": [],
        "backend_job_id": None,
        "backend_job_status": "idle",
        "backend_current_step": None,
        "backend_error": None,
        "backend_artifacts": [],
        "screenplay_data": {},
        "screenplay_yaml": "",
        "rendered_markdown": "",
        "audit_report": {},
    }

    data = _load_all()
    data["projects"].append(new_project)
    _save_all(data)
    return new_project


def update_project(project_id: str, updates: dict) -> dict | None:
    """
    更新指定项目的数据。
    updates 为要更新的字段字典，例如 {"original_text": "..."}。
    会自动更新 updated_at 时间戳。
    返回更新后的项目字典，找不到则返回 None。
    """
    data = _load_all()
    for project in data["projects"]:
        if project.get("id") == project_id:
            project.update(updates)
            project["updated_at"] = datetime.now().isoformat()
            _save_all(data)
            return project
    return None


def delete_project(project_id: str) -> bool:
    """
    删除指定项目。
    返回是否删除成功。
    """
    data = _load_all()
    original_len = len(data["projects"])
    data["projects"] = [p for p in data["projects"] if p.get("id") != project_id]
    if len(data["projects"]) < original_len:
        _save_all(data)
        return True
    return False

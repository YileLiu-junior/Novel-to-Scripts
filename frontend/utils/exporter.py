"""
exporter.py
将项目数据转换为结构化 YAML 剧本格式的工具模块。
"""

import yaml
from frontend.utils import storage


def _safe_filename(name: str) -> str:
    """
    将项目名称转换为安全的文件名（替换 Windows 不允许的字符）。
    """
    invalid_chars = '<>:"/\\|?*'
    for ch in invalid_chars:
        name = name.replace(ch, '_')
    return name.strip()


def _get_scene_name_by_id(project: dict, scene_id: str) -> str:
    """
    根据场景 id 获取场景名称。
    """
    if not scene_id:
        return "未选择场景"
    for scene in project.get("scenes", []):
        if scene.get("id") == scene_id:
            return scene.get("name", "未命名场景")
    return "未选择场景"


def _get_character_names_by_ids(project: dict, character_ids: list) -> list:
    """
    根据人物 id 列表获取人物名称列表。
    """
    if not character_ids:
        return []
    characters = project.get("characters", [])
    id_to_name = {c["id"]: c.get("name", "未命名") for c in characters}
    return [id_to_name.get(cid, "未知") for cid in character_ids if cid in id_to_name]


def build_script_yaml_data(project: dict) -> dict:
    """
    将项目数据转换为剧本 YAML 数据结构。

    :param project: 项目字典
    :return: 可序列化为 YAML 的字典
    """
    # 兼容旧数据
    original_text = project.get("original_text", "") or ""
    characters_list = project.get("characters", []) or []
    scenes_list = project.get("scenes", []) or []
    acts_list = project.get("acts", []) or []

    # 原文信息
    original_text_length = len(original_text)
    original_text_preview = original_text[:300] if original_text else ""

    # 人物映射
    yaml_characters = []
    for char in characters_list:
        yaml_characters.append({
            "id": char.get("id", ""),
            "name": char.get("name", "未命名"),
            "role": char.get("role", ""),
            "description": char.get("description", ""),
            "avatar": char.get("avatar", ""),
        })

    # 场景/演出背景映射（使用 settings 避免与 scene/场次混淆）
    yaml_settings = []
    for scene in scenes_list:
        yaml_settings.append({
            "id": scene.get("id", ""),
            "name": scene.get("name", "未命名场景"),
            "location": scene.get("location", ""),
            "description": scene.get("description", ""),
        })

    # 场次映射
    yaml_acts = []
    for act in acts_list:
        scene_id = act.get("scene_id", "") or ""
        character_ids = act.get("character_ids", []) or []
        yaml_acts.append({
            "id": act.get("id", ""),
            "title": act.get("title", "未命名场次"),
            "setting_id": scene_id,
            "setting_name": _get_scene_name_by_id(project, scene_id),
            "character_ids": character_ids,
            "characters": _get_character_names_by_ids(project, character_ids),
            "time": act.get("time", ""),
            "summary": act.get("summary", ""),
            "content": act.get("content", ""),
        })

    # 组装顶层结构
    data = {
        "schema_version": "1.0",
        "type": "novel_to_script",
        "project": {
            "id": project.get("id", ""),
            "title": project.get("name", "未命名项目"),
            "description": project.get("description", ""),
            "created_at": project.get("created_at", ""),
            "updated_at": project.get("updated_at", ""),
        },
        "source": {
            "original_text_length": original_text_length,
            "original_text_preview": original_text_preview,
        },
        "characters": yaml_characters,
        "settings": yaml_settings,
        "acts": yaml_acts,
    }

    return data


def dump_yaml(data: dict) -> str:
    """
    将 Python 字典转换为格式化的 YAML 字符串。

    :param data: 要序列化的字典
    :return: YAML 格式字符串
    """
    return yaml.safe_dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False)


def generate_yaml(project: dict) -> str:
    """
    一站式生成：项目数据 → YAML 字符串。

    :param project: 项目字典
    :return: YAML 格式字符串
    """
    data = build_script_yaml_data(project)
    return dump_yaml(data)


def get_download_filename(project: dict) -> str:
    """
    生成安全的下载文件名。

    :param project: 项目字典
    :return: 安全的文件名，如 "我的项目_script.yaml"
    """
    safe_name = _safe_filename(project.get("name", "未命名项目"))
    return f"{safe_name}_script.yaml"

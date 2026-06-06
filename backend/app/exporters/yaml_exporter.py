from __future__ import annotations

from typing import Any

#  yaml_exporter.py — YAML 序列化器

# 用途：将 Screenplay 聚合根序列化为 .yaml 剧本文件，或从 YAML 反序列化回来。对应 artifacts.py 中的 screenplay_yaml产物类型。

class YamlExporter:
    def export(self, data: dict[str, Any]) -> str:    # Python dict → YAML 字符串
        import yaml

        return yaml.safe_dump(data, allow_unicode=True, sort_keys=False)

    def parse(self, yaml_text: str) -> dict[str, Any]:   # YAML 字符串 → Python dict
        import yaml

        parsed = yaml.safe_load(yaml_text)
        if not isinstance(parsed, dict):
            raise ValueError("YAML root must be an object")
        return parsed


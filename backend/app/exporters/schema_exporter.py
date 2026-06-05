from __future__ import annotations

from pathlib import Path

# schema_exporter.py — JSON Schema 导出器
# 极其简单 —— 就是读取一个静态 JSON Schema 文件并返回其字符串内容。默认路径 schemas/screenplay.schema.json。
# 用途：对外暴露剧本的 JSON Schema 定义，前端/第三方可以据此做校验或代码生成。对应 API 路由 routes_schema.py。
class SchemaExporter:
    def __init__(self, schema_path: Path | None = None) -> None:     # 默认指向 schemas/screenplay.schema.json
        self.schema_path = schema_path or Path("schemas/screenplay.schema.json")

    def export_json_schema(self) -> str:      # 读取 schema 文件内容
        return self.schema_path.read_text(encoding="utf-8")


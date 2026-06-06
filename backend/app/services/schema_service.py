from __future__ import annotations

from app.exporters.schema_exporter import SchemaExporter


class SchemaService:
    def __init__(self, exporter: SchemaExporter | None = None) -> None:
        self.exporter = exporter or SchemaExporter()

    def download_schema(self) -> str:
        return self.exporter.export_json_schema()


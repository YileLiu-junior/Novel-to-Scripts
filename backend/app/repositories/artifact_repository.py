from __future__ import annotations

from pathlib import Path
from typing import Any

from app.domain.artifacts import Artifact
from app.repositories.file_store import default_data_root, ensure_directory, read_json, write_json_atomic, write_text_atomic


class ArtifactRepository:
    def __init__(self, data_root: Path | None = None) -> None:
        self.data_root = data_root or default_data_root()

    def _dir_for_project(self, project_id: str) -> Path:
        return self.data_root / "projects" / project_id / "artifacts"

    def _index_path(self, project_id: str) -> Path:
        return self._dir_for_project(project_id) / "index.json"

    def _artifact_path(self, artifact: Artifact) -> Path:
        suffix = "yaml" if artifact.type == "screenplay_yaml" else "json"
        return self._dir_for_project(artifact.project_id) / f"{artifact.type}_v{artifact.version:03d}.{suffix}"

    def _load_index(self, project_id: str) -> list[dict[str, Any]]:
        return read_json(self._index_path(project_id), [])

    def _save_index(self, project_id: str, records: list[dict[str, Any]]) -> None:
        write_json_atomic(self._index_path(project_id), records)

    def save(self, artifact: Artifact) -> Artifact:
        ensure_directory(self._dir_for_project(artifact.project_id))
        path = self._artifact_path(artifact)
        if isinstance(artifact.data, str):
            write_text_atomic(path, artifact.data)
        else:
            write_json_atomic(path, artifact.data)

        records = [record for record in self._load_index(artifact.project_id) if record["id"] != artifact.id]
        records.append(
            {
                "id": artifact.id,
                "project_id": artifact.project_id,
                "job_id": artifact.job_id,
                "type": artifact.type,
                "version": artifact.version,
                "path": path.name,
            }
        )
        records.sort(key=lambda record: (record["type"], record["version"], record["id"]))
        self._save_index(artifact.project_id, records)
        return artifact

    def list_for_project(self, project_id: str) -> list[Artifact]:
        return [self._artifact_from_record(project_id, record) for record in self._load_index(project_id)]

    def latest_for_project(self, project_id: str, artifact_type: str) -> Artifact | None:
        matches = [artifact for artifact in self.list_for_project(project_id) if artifact.type == artifact_type]
        if not matches:
            return None
        return max(matches, key=lambda artifact: artifact.version)

    def get(self, project_id: str, artifact_id_or_type: str) -> Artifact | None:
        artifacts = self.list_for_project(project_id)
        for artifact in artifacts:
            if artifact.id == artifact_id_or_type:
                return artifact
        return self.latest_for_project(project_id, artifact_id_or_type)

    def next_version(self, project_id: str, artifact_type: str) -> int:
        versions = [record["version"] for record in self._load_index(project_id) if record["type"] == artifact_type]
        return max(versions, default=0) + 1

    def _artifact_from_record(self, project_id: str, record: dict[str, Any]) -> Artifact:
        path = self._dir_for_project(project_id) / record["path"]
        if record["type"] == "screenplay_yaml":
            data: dict[str, Any] | str = path.read_text(encoding="utf-8")
        else:
            data = read_json(path, {})
        return Artifact(
            id=record["id"],
            project_id=record["project_id"],
            job_id=record.get("job_id"),
            type=record["type"],
            version=record["version"],
            data=data,
        )

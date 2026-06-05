from typing import Any

from pydantic import BaseModel


class ArtifactResponse(BaseModel):
    id: str
    type: str
    version: int
    data: dict[str, Any] | str


from fastapi import APIRouter

from app.api.dto.schema import SchemaResponse
from app.services.schema_service import SchemaService

router = APIRouter()


@router.get("/{project_id}/schema/download", response_model=SchemaResponse)
def download_schema(project_id: str) -> SchemaResponse:
    return SchemaResponse(schema_text=SchemaService().download_schema())


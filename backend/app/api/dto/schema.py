from pydantic import BaseModel


class SchemaResponse(BaseModel):
    schema_text: str
    content_type: str = "application/schema+json"


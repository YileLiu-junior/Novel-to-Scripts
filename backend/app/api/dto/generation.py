from pydantic import BaseModel

from app.domain.adaptation import AdaptationConfig


class GenerateRequest(BaseModel):
    adaptation_config: AdaptationConfig = AdaptationConfig()


class GenerateResponse(BaseModel):
    job_id: str
    status: str


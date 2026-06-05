from fastapi import APIRouter

from app.api.dto.generation import GenerateRequest, GenerateResponse

router = APIRouter()


@router.post("/{project_id}/generate/story-bible", response_model=GenerateResponse)
def generate_story_bible(project_id: str, request: GenerateRequest) -> GenerateResponse:
    return GenerateResponse(job_id=f"job_{project_id}_story_bible", status="queued")


@router.post("/{project_id}/generate/adaptation-plan", response_model=GenerateResponse)
def generate_adaptation_plan(project_id: str, request: GenerateRequest) -> GenerateResponse:
    return GenerateResponse(job_id=f"job_{project_id}_adaptation_plan", status="queued")


@router.post("/{project_id}/generate/screenplay", response_model=GenerateResponse)
def generate_screenplay(project_id: str, request: GenerateRequest) -> GenerateResponse:
    return GenerateResponse(job_id=f"job_{project_id}_screenplay", status="queued")


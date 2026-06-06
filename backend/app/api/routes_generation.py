from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.api.dto.generation import GenerateRequest, GenerateResponse
from app.services.chapter_service import ChapterService
from app.services.generation_orchestrator import GenerationOrchestrator
from app.services.job_service import JobService
from app.services.project_service import ProjectService
from app.workers.jobs import enqueue_generation

router = APIRouter()


@router.post("/{project_id}/generate/story-bible", response_model=GenerateResponse)
def generate_story_bible(project_id: str, request: GenerateRequest) -> GenerateResponse:
    return GenerateResponse(job_id=f"job_{project_id}_story_bible", status="queued")


@router.post("/{project_id}/generate/adaptation-plan", response_model=GenerateResponse)
def generate_adaptation_plan(project_id: str, request: GenerateRequest) -> GenerateResponse:
    return GenerateResponse(job_id=f"job_{project_id}_adaptation_plan", status="queued")


@router.post("/{project_id}/generate/screenplay", response_model=GenerateResponse)
def generate_screenplay(
    project_id: str,
    request: GenerateRequest,
    background_tasks: BackgroundTasks,
) -> GenerateResponse:
    if ProjectService().get_project(project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    chapter_service = ChapterService()
    chapters = chapter_service.list_for_project(project_id)
    findings = chapter_service.validate_generation_ready(chapters)
    errors = [finding for finding in findings if finding.severity == "error"]
    if errors:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "cannot-generate",
                "message": errors[0].message,
                "findings": [finding.model_dump(mode="json") for finding in findings],
            },
        )

    job = JobService().create_job(project_id)
    enqueue_generation(
        background_tasks,
        GenerationOrchestrator.from_provider_settings(),
        project_id,
        [chapter.model_dump(mode="json") for chapter in chapters],
        request.adaptation_config,
        job,
    )
    return GenerateResponse(job_id=job.id, status=job.status)

from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.api.dto.generation import GenerateRequest, GenerateResponse
from app.services.chapter_service import ChapterService
from app.services.generation_orchestrator import GenerationOrchestrator
from app.services.job_service import JobService
from app.services.project_service import ProjectService
from app.workers.jobs import enqueue_adaptation_plan, enqueue_generation, enqueue_story_bible

router = APIRouter()


def _prepare_generation(project_id: str) -> tuple[list[dict], GenerationOrchestrator]:
    """校验项目存在且章节满足最低生成要求，返回章节列表与 orchestrator。"""
    if ProjectService().get_project(project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    chapter_service = ChapterService()
    chapters = chapter_service.list_for_project(project_id)
    findings = chapter_service.validate_generation_ready(chapters)
    errors = [f for f in findings if f.severity == "error"]
    if errors:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "cannot-generate",
                "message": errors[0].message,
                "findings": [f.model_dump(mode="json") for f in findings],
            },
        )

    orchestrator = GenerationOrchestrator.from_provider_settings()
    chapter_dicts = [ch.model_dump(mode="json") for ch in chapters]
    return chapter_dicts, orchestrator


@router.post("/{project_id}/generate/story-bible", response_model=GenerateResponse)
def generate_story_bible(
    project_id: str,
    request: GenerateRequest,
    background_tasks: BackgroundTasks,
) -> GenerateResponse:
    """运行 novel_reader → story_ontology，生成并保存 story_bible artifact。

    产物: story_bible, novel_analysis
    """
    chapters, orchestrator = _prepare_generation(project_id)
    job = JobService().create_job(project_id)
    enqueue_story_bible(
        background_tasks,
        orchestrator,
        project_id,
        chapters,
        request.adaptation_config,
        job,
    )
    return GenerateResponse(job_id=job.id, status=job.status)


@router.post("/{project_id}/generate/adaptation-plan", response_model=GenerateResponse)
def generate_adaptation_plan(
    project_id: str,
    request: GenerateRequest,
    background_tasks: BackgroundTasks,
) -> GenerateResponse:
    """运行 novel_reader → story_ontology → adaptation_planner，生成并保存 adaptation_plan。

    产物: story_bible, novel_analysis, adaptation_plan
    """
    chapters, orchestrator = _prepare_generation(project_id)
    job = JobService().create_job(project_id)
    enqueue_adaptation_plan(
        background_tasks,
        orchestrator,
        project_id,
        chapters,
        request.adaptation_config,
        job,
    )
    return GenerateResponse(job_id=job.id, status=job.status)


@router.post("/{project_id}/generate/screenplay", response_model=GenerateResponse)
def generate_screenplay(
    project_id: str,
    request: GenerateRequest,
    background_tasks: BackgroundTasks,
) -> GenerateResponse:
    """运行完整的 4 阶段改编流水线: novel_reader → story_ontology → adaptation_planner → screenplay_writer。

    产物: story_bible, screenplay_json, screenplay_yaml, audit_report,
          screenplay_rendered (.md/.txt)
    """
    chapters, orchestrator = _prepare_generation(project_id)
    job = JobService().create_job(project_id)
    enqueue_generation(
        background_tasks,
        orchestrator,
        project_id,
        chapters,
        request.adaptation_config,
        job,
    )
    return GenerateResponse(job_id=job.id, status=job.status)

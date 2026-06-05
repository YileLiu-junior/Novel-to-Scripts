from __future__ import annotations

from typing import Any

from app.ai.skills.adaptation_planner import AdaptationPlannerSkill
from app.ai.skills.novel_reader import NovelReaderSkill
from app.ai.skills.screenplay_writer import ScreenplayYamlWriterSkill
from app.ai.skills.story_ontology import StoryOntologySkill
from app.domain.adaptation import AdaptationConfig
from app.domain.jobs import GenerationJob
from app.services.artifact_service import ArtifactService
from app.services.job_service import JobService
from app.services.llm_trace_service import LlmTraceService
from app.services.validation_service import ValidationService
from app.services.yaml_service import YamlService


class GenerationOrchestrator:
    def __init__(
        self,
        novel_reader: NovelReaderSkill,
        story_ontology: StoryOntologySkill,
        adaptation_planner: AdaptationPlannerSkill,
        screenplay_writer: ScreenplayYamlWriterSkill,
        artifact_service: ArtifactService | None = None,
        job_service: JobService | None = None,
        llm_trace_service: LlmTraceService | None = None,
        validation_service: ValidationService | None = None,
        yaml_service: YamlService | None = None,
    ) -> None:
        self.novel_reader = novel_reader
        self.story_ontology = story_ontology
        self.adaptation_planner = adaptation_planner
        self.screenplay_writer = screenplay_writer
        self.artifact_service = artifact_service or ArtifactService()
        self.job_service = job_service or JobService()
        self.llm_trace_service = llm_trace_service or LlmTraceService()
        self.validation_service = validation_service or ValidationService()
        self.yaml_service = yaml_service or YamlService(validation_service=self.validation_service)

    def run_v1(
        self,
        project_id: str,
        chapters: list[dict[str, Any]],
        adaptation_config: AdaptationConfig,
        job: GenerationJob | None = None,
    ) -> GenerationJob:
        active_job = job or self.job_service.create_job(project_id)
        try:
            active_job = self.job_service.mark_step(active_job, "running", "novel_reader")
            novel_analysis = self.novel_reader.run({"chapters": chapters})
            self.artifact_service.save_artifact(project_id, "novel_analysis", novel_analysis, active_job.id)
            self.llm_trace_service.record_fake_run(active_job.id, "novel_reader", novel_analysis)

            active_job = self.job_service.mark_step(active_job, "running", "story_ontology")
            story_assets = self.story_ontology.run(novel_analysis)
            self.artifact_service.save_artifact(project_id, "story_bible", story_assets, active_job.id)

            active_job = self.job_service.mark_step(active_job, "running", "adaptation_planner")
            adaptation_plan = self.adaptation_planner.run(
                {
                    **story_assets,
                    "adaptation_config": adaptation_config.model_dump(),
                }
            )
            self.artifact_service.save_artifact(project_id, "adaptation_plan", adaptation_plan, active_job.id)

            active_job = self.job_service.mark_step(active_job, "running", "screenplay_writer")
            screenplay_json = self.screenplay_writer.run(
                {
                    **story_assets,
                    "adaptation_config": adaptation_config.model_dump(),
                    "adaptation_plan": adaptation_plan,
                }
            )
            findings = self.validation_service.validate_screenplay(screenplay_json)
            audit_report = self.validation_service.audit_report_for(findings).model_dump()
            screenplay_json["audit_report"] = audit_report
            yaml_text = self.yaml_service.export_validated(screenplay_json)
            self.artifact_service.save_artifact(project_id, "screenplay_json", screenplay_json, active_job.id)
            self.artifact_service.save_artifact(project_id, "screenplay_yaml", yaml_text, active_job.id)
            self.artifact_service.save_artifact(project_id, "audit_report", audit_report, active_job.id)
            return self.job_service.mark_step(active_job, "succeeded", "complete")
        except Exception as exc:
            return self.job_service.mark_step(active_job, "failed", active_job.current_step, str(exc))


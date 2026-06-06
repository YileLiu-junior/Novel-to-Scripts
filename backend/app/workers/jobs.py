from __future__ import annotations

from fastapi import BackgroundTasks

from app.domain.adaptation import AdaptationConfig
from app.domain.jobs import GenerationJob
from app.services.generation_orchestrator import GenerationOrchestrator

# 一行代码把整个改编流水线丢进 FastAPI 的后台任务队列
# 为什么需要这一层

#   ┌───────────────────────────────────────────────────────┬──────────────────────────────────────────┐
#   │                         问题                          │                   解决                   │
#   ├───────────────────────────────────────────────────────┼──────────────────────────────────────────┤
#   │ 改编流水线要调 4 轮 LLM，耗时很长                     │ 不能阻塞 HTTP 响应，必须异步执行         │
#   ├───────────────────────────────────────────────────────┼──────────────────────────────────────────┤
#   │ 路由层不应直接知道后台任务细节                        │ 用 enqueue_generation 封装，路由只传参数 │
#   ├───────────────────────────────────────────────────────┼──────────────────────────────────────────┤
#   │ FastAPI BackgroundTasks 的 API 是 add_task(fn, *args) │ 这个薄封装让调用方不关心底层机制         │
#   └───────────────────────────────────────────────────────┴──────────────────────────────────────────┘

#   调用链

#   路由 POST /projects/{id}/generate
#       → enqueue_generation(background_tasks, orchestrator, ...)
#           → background_tasks.add_task(orchestrator.run_v1, ...)
#               → 立即返回 202 Accepted + job_id
#               → 后台执行 4 阶段流水线（novel_reader → story_ontology → adaptation_planner → screenplay_writer）

#   这是一个**（fire-and-forget）**的模式——路由拿到 job_id 立刻响应给前端，后台慢慢跑，前端通过 /jobs/{id} 轮询状态。
def enqueue_generation(
    background_tasks: BackgroundTasks,
    orchestrator: GenerationOrchestrator,
    project_id: str,
    chapters: list[dict],
    adaptation_config: AdaptationConfig,
    job: GenerationJob,
) -> None:
    background_tasks.add_task(orchestrator.run_v1, project_id, chapters, adaptation_config, job)

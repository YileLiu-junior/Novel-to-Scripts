from fastapi import APIRouter

from app.api import (
    routes_artifacts,
    routes_chapters,
    routes_generation,
    routes_health,
    routes_jobs,
    routes_projects,
    routes_schema,
    routes_yaml,
)

api_router = APIRouter()
api_router.include_router(routes_health.router, tags=["health"])
api_router.include_router(routes_projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(routes_chapters.router, prefix="/projects", tags=["chapters"])
api_router.include_router(routes_generation.router, prefix="/projects", tags=["generation"])
api_router.include_router(routes_artifacts.router, prefix="/projects", tags=["artifacts"])
api_router.include_router(routes_yaml.router, prefix="/projects", tags=["yaml"])
api_router.include_router(routes_schema.router, prefix="/projects", tags=["schema"])
api_router.include_router(routes_jobs.router, prefix="/jobs", tags=["jobs"])


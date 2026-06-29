from fastapi import APIRouter

from app.api.v1 import evaluation, health, intelligence, report, repositories

router = APIRouter(prefix="/api/v1")
router.include_router(health.router, tags=["health"])
router.include_router(repositories.router)
router.include_router(intelligence.router)
router.include_router(evaluation.router)
router.include_router(report.router)

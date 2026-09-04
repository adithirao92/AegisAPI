"""Aggregates all v1 route modules into a single API router."""

from fastapi import APIRouter

from app.api.v1.routes.ai import router as ai_router
from app.api.v1.routes.specs import router as specs_router

router = APIRouter(prefix="/api/v1")
router.include_router(ai_router)
router.include_router(specs_router)

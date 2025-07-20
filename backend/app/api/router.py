from fastapi import APIRouter
from app.api.endpoints import health, transcription, content
from app.config.settings import settings

# Create the main router
router = APIRouter(prefix=settings.API_V1_PREFIX)

# Include all endpoint routers
router.include_router(health.router, tags=["health"])
router.include_router(transcription.router, tags=["transcription"])
router.include_router(content.router, prefix="/content", tags=["content"]) 
"""API endpoints package"""
from fastapi import APIRouter
from app.api.endpoints import health, content, transcription

# Create main router
router = APIRouter()

# Include all endpoint routers
router.include_router(health.router, tags=["health"])
router.include_router(content.router, prefix="/content", tags=["content"])
router.include_router(transcription.router, prefix="/transcription", tags=["transcription"]) 
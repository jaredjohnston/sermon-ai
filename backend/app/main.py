import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import router as api_router
from app.config.settings import settings
from app.services.startup_service import startup_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_application() -> FastAPI:
    """Create and configure the FastAPI application"""
    
    # Create FastAPI app
    app = FastAPI(
        title="Sermon AI",
        description="API for processing and generating content from sermon videos",
        version="1.0.0"
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, replace with specific origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include API routes
    app.include_router(api_router, prefix="/api/v1")
    
    # Add startup and shutdown event handlers
    @app.on_event("startup")
    async def startup_event():
        """Initialize application services on startup"""
        await startup_service.initialize_application()
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """Shutdown application services gracefully"""
        await startup_service.shutdown_application()
    
    return app

app = create_application()

@app.get("/")
async def root():
    """Root endpoint returning API information"""
    return {
        "name": "Sermon AI API",
        "version": "1.0.0",
        "status": "active",
        "documentation": "/docs"
    } 
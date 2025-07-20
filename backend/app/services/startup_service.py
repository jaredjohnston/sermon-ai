import asyncio
import logging
from app.services.background_job_service import background_job_service

logger = logging.getLogger(__name__)

class StartupService:
    """Service for handling application startup tasks"""
    
    def __init__(self):
        self.startup_complete = False
        
    async def initialize_application(self):
        """Initialize the application with background services"""
        if self.startup_complete:
            logger.warning("Application already initialized")
            return
            
        try:
            logger.info("🚀 Starting application initialization...")
            
            # Start background job workers
            await background_job_service.start_workers(num_workers=2)
            
            self.startup_complete = True
            logger.info("✅ Application initialization complete")
            
        except Exception as e:
            logger.error(f"❌ Application initialization failed: {str(e)}", exc_info=True)
            raise
            
    async def shutdown_application(self):
        """Shutdown the application gracefully"""
        if not self.startup_complete:
            logger.warning("Application not initialized, skipping shutdown")
            return
            
        try:
            logger.info("🛑 Starting application shutdown...")
            
            # Stop background job workers
            await background_job_service.stop_workers()
            
            self.startup_complete = False
            logger.info("✅ Application shutdown complete")
            
        except Exception as e:
            logger.error(f"❌ Application shutdown failed: {str(e)}", exc_info=True)

# Global singleton instance
startup_service = StartupService()
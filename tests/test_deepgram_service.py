import asyncio
import logging
from app.services.deepgram_service import deepgram_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_service():
    """Test the Deepgram service with a test file"""
    try:
        # Open the test file
        with open("test_audio.mp4", "rb") as file:
            logger.info("Starting transcription test...")
            
            # Call the service with video/mp4 content type
            result = await deepgram_service.transcribe_file(
                file=file,
                content_type="video/mp4"
            )
            
            logger.info("Transcription started successfully!")
            logger.info(f"Request ID: {result['request_id']}")
            logger.info(f"Callback URL: {result['callback_url']}")
            logger.info(f"Status: {result['status']}")
            
            # Keep script running to receive callback
            logger.info("\nWaiting for callback (this may take a few minutes)...")
            for _ in range(600):  # Wait up to 10 minutes
                await asyncio.sleep(1)
                print(".", end="", flush=True)
                
    except Exception as e:
        logger.error(f"Test failed!")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error message: {str(e)}")
        if hasattr(e, 'response'):
            logger.error(f"Response status: {e.response.status_code}")
            logger.error(f"Response body: {e.response.text}")
        raise

if __name__ == "__main__":
    print("\nℹ️  Make sure your FastAPI app is running with ngrok!")
    print("   1. Start the app: uvicorn app.main:app --reload")
    print("   2. Start ngrok: ngrok http 8000")
    
    # Run the test
    asyncio.run(test_service()) 
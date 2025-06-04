import logging
from fastapi import APIRouter, HTTPException, status
from app.models.schemas import ContentGenerationRequest, ContentGenerationResponse
from app.services.content_service import content_service

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/generate", response_model=ContentGenerationResponse)
async def generate_content(request: ContentGenerationRequest):
    """
    Generate content from classified sermon segments
    """
    try:
        logger.info(
            f"Received content generation request for {len(request.segments)} segments "
            f"to generate {request.content_type}"
        )
        
        content = await content_service.generate_content(
            segments=request.segments,
            content_type=request.content_type
        )
        
        return ContentGenerationResponse(
            content=content,
            metadata={
                "segments_used": len(request.segments),
                "content_type": request.content_type
            }
        )
        
    except Exception as e:
        logger.error(f"Content generation error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Content generation failed: {str(e)}"
        ) 
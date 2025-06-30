import logging
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, status, Depends
from app.models.schemas import (
    ContentGenerationRequest, ContentGenerationResponse,
    ContentTemplate, ContentTemplateCreate, ContentTemplateUpdate,
    GeneratedContentModel, TemplateStatus,
    TemplateExtractionRequest, TemplateExtractionResponse
)
from app.services.content_service import content_service
from app.services.template_service import template_service, TemplateServiceError
from app.middleware.auth import get_current_user
from app.models.schemas import User

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

# Content Template Management Endpoints

@router.post("/templates", response_model=ContentTemplate, status_code=status.HTTP_201_CREATED)
async def create_template(
    template: ContentTemplateCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new content template"""
    try:
        logger.info(f"Creating content template '{template.name}' for client {template.client_id}")
        
        created_template = await template_service.create_template(template, current_user.id)
        
        logger.info(f"Content template created successfully: {created_template.id}")
        return created_template
        
    except TemplateServiceError as e:
        logger.error(f"Template creation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error creating template: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create template"
        )

@router.get("/templates", response_model=List[ContentTemplate])
async def list_templates(
    status_filter: Optional[TemplateStatus] = None,
    content_type_name: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """List all content templates for the user's organization"""
    try:
        logger.info(f"Listing templates for user {current_user.id}")
        
        templates = await template_service.list_templates(
            current_user.id, 
            status=status_filter,
            content_type_name=content_type_name
        )
        
        logger.info(f"Found {len(templates)} templates")
        return templates
        
    except TemplateServiceError as e:
        logger.error(f"Template listing error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error listing templates: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list templates"
        )

@router.get("/templates/{template_id}", response_model=ContentTemplate)
async def get_template(
    template_id: UUID,
    current_user: User = Depends(get_current_user)
):
    """Get a specific content template by ID"""
    try:
        logger.info(f"Getting template {template_id} for user {current_user.id}")
        
        template = await template_service.get_template(template_id, current_user.id)
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template {template_id} not found"
            )
        
        return template
        
    except HTTPException:
        raise
    except TemplateServiceError as e:
        logger.error(f"Template retrieval error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error getting template: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get template"
        )

@router.put("/templates/{template_id}", response_model=ContentTemplate)
async def update_template(
    template_id: UUID,
    updates: ContentTemplateUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update a content template"""
    try:
        logger.info(f"Updating template {template_id} for user {current_user.id}")
        
        updated_template = await template_service.update_template(
            template_id, updates, current_user.id
        )
        
        logger.info(f"Template updated successfully: {template_id}")
        return updated_template
        
    except TemplateServiceError as e:
        logger.error(f"Template update error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error updating template: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update template"
        )

@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: UUID,
    current_user: User = Depends(get_current_user)
):
    """Delete a content template (soft delete)"""
    try:
        logger.info(f"Deleting template {template_id} for user {current_user.id}")
        
        success = await template_service.delete_template(template_id, current_user.id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template {template_id} not found"
            )
        
        logger.info(f"Template deleted successfully: {template_id}")
        
    except HTTPException:
        raise
    except TemplateServiceError as e:
        logger.error(f"Template deletion error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error deleting template: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete template"
        )

# Generated Content Endpoints

@router.get("/transcripts/{transcript_id}/generated", response_model=List[GeneratedContentModel])
async def list_generated_content_for_transcript(
    transcript_id: UUID,
    current_user: User = Depends(get_current_user)
):
    """List all generated content for a specific transcript"""
    try:
        logger.info(f"Listing generated content for transcript {transcript_id}")
        
        content_list = await template_service.list_generated_content_by_transcript(
            transcript_id, current_user.id
        )
        
        logger.info(f"Found {len(content_list)} generated content items")
        return content_list
        
    except TemplateServiceError as e:
        logger.error(f"Generated content listing error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error listing generated content: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list generated content"
        )

@router.get("/generated/{content_id}", response_model=GeneratedContentModel)
async def get_generated_content(
    content_id: UUID,
    current_user: User = Depends(get_current_user)
):
    """Get specific generated content by ID"""
    try:
        logger.info(f"Getting generated content {content_id}")
        
        content = await template_service.get_generated_content(content_id, current_user.id)
        
        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Generated content {content_id} not found"
            )
        
        return content
        
    except HTTPException:
        raise
    except TemplateServiceError as e:
        logger.error(f"Generated content retrieval error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error getting generated content: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get generated content"
        )

# Placeholder for Phase 2: Pattern Extraction Endpoint
# This will be implemented in Phase 2 along with pattern_extraction_service.py

@router.post("/templates/extract", response_model=TemplateExtractionResponse)
async def extract_template_patterns(
    request: TemplateExtractionRequest,
    current_user: User = Depends(get_current_user)
):
    """Extract content patterns from examples to create structured prompts"""
    # TODO: Implement in Phase 2 with pattern_extraction_service
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Pattern extraction feature coming in Phase 2"
    ) 
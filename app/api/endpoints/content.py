import logging
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, status, Depends
from app.models.schemas import (
    ContentGenerationRequest, ContentGenerationResponse,
    ContentTemplate, ContentTemplateCreate, ContentTemplateUpdate, ContentTemplatePublic,
    GeneratedContentModel, TemplateStatus,
    TemplateExtractionRequest, TemplateExtractionResponse
)
from app.services.content_service import content_service
from app.services.template_service import template_service, TemplateServiceError
from app.services.supabase_service import supabase_service, NotFoundError
from app.middleware.auth import get_current_user, get_auth_context, AuthContext
from app.models.schemas import User
from app.config.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter()


# Content Template Management Endpoints

@router.post("/templates", response_model=ContentTemplatePublic, status_code=status.HTTP_201_CREATED)
async def create_template(
    template: ContentTemplateCreate,
    auth: AuthContext = Depends(get_auth_context)
):
    """Create a new content template"""
    try:
        logger.info(f"Creating content template '{template.name}' for client {template.client_id}")
        
        created_template = await template_service.create_template(
            template, auth.user.id, auth.access_token
        )
        
        logger.info(f"Content template created successfully: {created_template.id}")
        
        # Return public version (excludes structured_prompt)
        return ContentTemplatePublic(**created_template.dict())
        
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

@router.get("/templates", response_model=List[ContentTemplatePublic])
async def list_templates(
    status_filter: Optional[TemplateStatus] = None,
    content_type_name: Optional[str] = None,
    auth: AuthContext = Depends(get_auth_context)
):
    """List all content templates for the user's organization"""
    try:
        logger.info(f"Listing templates for user {auth.user.id}")
        
        templates = await template_service.list_templates(
            auth.user.id, 
            auth.access_token,
            status=status_filter,
            content_type_name=content_type_name
        )
        
        logger.info(f"Found {len(templates)} templates")
        
        # Return public versions (excludes structured_prompt)
        return [ContentTemplatePublic(**template.dict()) for template in templates]
        
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

@router.get("/templates/{template_id}", response_model=ContentTemplatePublic)
async def get_template(
    template_id: UUID,
    auth: AuthContext = Depends(get_auth_context)
):
    """Get a specific content template by ID"""
    try:
        logger.info(f"Getting template {template_id} for user {auth.user.id}")
        
        template = await template_service.get_template(
            template_id, auth.user.id, auth.access_token
        )
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template {template_id} not found"
            )
        
        # Return public version (excludes structured_prompt)
        return ContentTemplatePublic(**template.dict())
        
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

@router.put("/templates/{template_id}", response_model=ContentTemplatePublic)
async def update_template(
    template_id: UUID,
    updates: ContentTemplateUpdate,
    auth: AuthContext = Depends(get_auth_context)
):
    """Update a content template"""
    try:
        logger.info(f"Updating template {template_id} for user {auth.user.id}")
        
        updated_template = await template_service.update_template(
            template_id, updates, auth.user.id, auth.access_token
        )
        
        logger.info(f"Template updated successfully: {template_id}")
        
        # Return public version (excludes structured_prompt)
        return ContentTemplatePublic(**updated_template.dict())
        
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
    auth: AuthContext = Depends(get_auth_context)
):
    """Delete a content template (soft delete)"""
    try:
        logger.info(f"Deleting template {template_id} for user {auth.user.id}")
        
        success = await template_service.delete_template(
            template_id, auth.user.id, auth.access_token
        )
        
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
    auth: AuthContext = Depends(get_auth_context)
):
    """List all generated content for a specific transcript"""
    try:
        logger.info(f"Listing generated content for transcript {transcript_id}")
        
        content_list = await template_service.list_generated_content_by_transcript(
            transcript_id, auth.user.id, auth.access_token
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
    auth: AuthContext = Depends(get_auth_context)
):
    """Get specific generated content by ID"""
    try:
        logger.info(f"Getting generated content {content_id}")
        
        content = await template_service.get_generated_content(
            content_id, auth.user.id, auth.access_token
        )
        
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

@router.post("/templates/extract", response_model=TemplateExtractionResponse)
async def extract_template_patterns(
    request: TemplateExtractionRequest,
    auth: AuthContext = Depends(get_auth_context)
):
    """Extract content patterns from examples to create structured prompts"""
    try:
        logger.info(f"Extracting patterns for {request.content_type_name} with {len(request.examples)} examples")
        
        # Import here to avoid circular imports
        from app.services.pattern_extraction_service import pattern_extraction_service, PatternExtractionError
        
        # Validate user has access to a client
        user_client = await supabase_service.get_user_client(auth.user.id)
        if not user_client:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User must belong to a client to extract patterns"
            )
        
        # Extract patterns from examples
        analysis_result = await pattern_extraction_service.extract_patterns(
            examples=request.examples,
            content_type_name=request.content_type_name,
            description=request.description
        )
        
        # Generate structured prompt from analysis
        structured_prompt = await pattern_extraction_service.generate_structured_prompt(analysis_result)
        
        # Validate confidence threshold
        min_confidence = getattr(settings, 'PATTERN_CONFIDENCE_THRESHOLD', 0.7)
        if analysis_result.confidence_score < min_confidence:
            logger.warning(
                f"Low confidence score: {analysis_result.confidence_score:.3f} < {min_confidence} "
                f"for {request.content_type_name}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Pattern extraction confidence too low ({analysis_result.confidence_score:.2f}). "
                    f"Please provide more consistent examples or add more examples."
                )
            )
        
        logger.info(
            f"Pattern extraction successful for {request.content_type_name}: "
            f"confidence={analysis_result.confidence_score:.3f}, "
            f"prompt_length={len(structured_prompt)}"
        )
        
        # Return the structured prompt and analysis metadata
        return TemplateExtractionResponse(
            structured_prompt=structured_prompt,
            confidence_score=analysis_result.confidence_score,
            extracted_patterns={
                "style_patterns": analysis_result.style_patterns,
                "structure_patterns": analysis_result.structure_patterns,
                "tone_analysis": analysis_result.tone_analysis,
                "format_requirements": analysis_result.format_requirements,
                "analysis_metadata": analysis_result.analysis_metadata
            }
        )
        
    except PatternExtractionError as e:
        logger.error(f"Pattern extraction error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Pattern extraction failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error in pattern extraction: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to extract patterns from examples"
        )

@router.post("/generate-with-template", response_model=ContentGenerationResponse, status_code=status.HTTP_201_CREATED)
async def generate_content_with_template(
    request: ContentGenerationRequest,
    auth: AuthContext = Depends(get_auth_context)
):
    """Generate content using a custom template from a transcript"""
    try:
        logger.info(f"Generating content with template {request.template_id} for transcript {request.transcript_id}")
        
        # Get the template and verify access
        template = await template_service.get_template(
            request.template_id, auth.user.id, auth.access_token
        )
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template {request.template_id} not found"
            )
        
        # Get the transcript and verify access
        try:
            transcript = await supabase_service.get_transcript(
                request.transcript_id, auth.user.id
            )
            if not transcript:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Transcript {request.transcript_id} not found"
                )
        except NotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Transcript {request.transcript_id} not found"
            )
        
        # Extract full transcript from Deepgram response
        if not transcript.raw_transcript:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Transcript has no raw data available"
            )
        
        try:
            full_transcript = content_service.extract_full_transcript_from_deepgram(
                transcript.raw_transcript
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid transcript data: {str(e)}"
            )
        
        # Generate content using template and full transcript
        generation_result = await content_service.generate_content_with_template(
            full_transcript=full_transcript,
            template=template,
            custom_instructions=request.custom_instructions
        )
        
        # Create generated content record
        from app.models.schemas import GeneratedContentCreate
        generated_content_data = GeneratedContentCreate(
            client_id=template.client_id,
            transcript_id=request.transcript_id,
            template_id=request.template_id,
            content=generation_result["content"],
            content_metadata=generation_result["content_metadata"],
            generation_settings=generation_result["generation_settings"],
            generation_cost_cents=generation_result["generation_cost_cents"],
            generation_duration_ms=generation_result["generation_duration_ms"]
        )
        
        # Save to database
        saved_content = await template_service.create_generated_content(
            generated_content_data, auth.user.id, auth.access_token
        )
        
        logger.info(f"Content generated successfully: {saved_content.id}")
        
        return ContentGenerationResponse(
            id=saved_content.id,
            content=saved_content.content,
            metadata=saved_content.content_metadata,
            generation_cost_cents=saved_content.generation_cost_cents,
            generation_duration_ms=saved_content.generation_duration_ms
        )
        
    except HTTPException:
        raise
    except TemplateServiceError as e:
        logger.error(f"Template service error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error generating content with template: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate content with template"
        )

# Onboarding-Specific Endpoints

@router.post("/onboarding/extract-and-create-template", response_model=ContentTemplatePublic, status_code=status.HTTP_201_CREATED)
async def onboarding_extract_and_create_template(
    request: TemplateExtractionRequest,
    auth: AuthContext = Depends(get_auth_context)
):
    """
    Onboarding wizard: Extract patterns from examples and automatically create template
    This combines pattern extraction + template creation in one step for smooth UX
    """
    try:
        logger.info(f"Onboarding: Extracting patterns and creating template for user {auth.user.id}")
        
        # Import here to avoid circular imports
        from app.services.pattern_extraction_service import pattern_extraction_service, PatternExtractionError
        
        # Validate user has access to a client
        user_client = await supabase_service.get_user_client(auth.user.id)
        if not user_client:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User must belong to a client to create templates"
            )
        
        # Validate that user provided content type name
        if not request.content_type_name or not request.content_type_name.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Content type name is required. Please describe what type of content you want to create (e.g., 'small group guide', 'Facebook post')."
            )
        
        # Extract patterns using user-defined content type
        analysis_result = await pattern_extraction_service.extract_patterns(
            examples=request.examples,
            content_type_name=request.content_type_name.strip(),
            description=request.description
        )
        
        # Generate structured prompt from analysis
        structured_prompt = await pattern_extraction_service.generate_structured_prompt(analysis_result)
        
        # Use relaxed confidence threshold for onboarding (learning mode)
        min_confidence = getattr(settings, 'ONBOARDING_CONFIDENCE_THRESHOLD', 0.6)
        if analysis_result.confidence_score < min_confidence:
            logger.warning(
                f"Low confidence score during onboarding: {analysis_result.confidence_score:.3f} < {min_confidence} "
                f"for {analysis_result.content_type}"
            )
            # For onboarding, we'll proceed but warn the user
        
        # Auto-create template name from user's content type
        template_name = f"My {request.content_type_name.title()}"
        
        # Create template automatically
        from app.models.schemas import ContentTemplateCreate
        template_data = ContentTemplateCreate(
            client_id=user_client.id,
            name=template_name,
            description=f"Custom template created during onboarding for {request.content_type_name}",
            content_type_name=request.content_type_name.strip(),
            structured_prompt=structured_prompt,
            example_content=request.examples,
            status="active",
            model_settings={
                "temperature": 0.7,
                "max_tokens": 2000,
                "model": "gpt-4o"
            }
        )
        
        # Create the template
        created_template = await template_service.create_template(
            template_data, auth.user.id, auth.access_token
        )
        
        logger.info(
            f"Onboarding template created successfully: {created_template.id} "
            f"for content type '{request.content_type_name}' "
            f"with confidence {analysis_result.confidence_score:.3f}"
        )
        
        # Return public version (excludes structured_prompt)
        return ContentTemplatePublic(**created_template.dict())
        
    except PatternExtractionError as e:
        logger.error(f"Onboarding pattern extraction error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to extract patterns: {str(e)}"
        )
    except TemplateServiceError as e:
        logger.error(f"Onboarding template creation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create template: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error in onboarding flow: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete onboarding template creation"
        )

@router.get("/onboarding/demo-transcript")
async def get_demo_transcript():
    """
    Get demo transcript for onboarding content generation
    TODO: Replace with actual demo content
    """
    return {
        "transcript_id": "demo-transcript",
        "title": "Demo Sermon: Walking in Faith",
        "transcript": """
        Good morning, everyone. Today we're going to explore what it means to walk in faith, 
        even when the path ahead seems uncertain. Turn with me to Hebrews chapter 11, verse 1...
        
        Faith is the assurance of things hoped for, the conviction of things not seen. 
        This powerful verse reminds us that faith isn't about having all the answers, 
        but about trusting in God's goodness even when we can't see the whole picture...
        
        Let me share a story about a woman in our community who exemplified this kind of faith...
        [Continue with sermon content...]
        
        As we close today, I want to challenge each of you to take one step of faith this week...
        """,
        "metadata": {
            "speaker": "Pastor Demo",
            "date": "2024-01-15",
            "series": "Faith in Action",
            "duration_minutes": 25
        }
    }

@router.post("/onboarding/generate-demo-content/{template_id}", response_model=ContentGenerationResponse)
async def generate_demo_content(
    template_id: UUID,
    auth: AuthContext = Depends(get_auth_context)
):
    """
    Generate content using the user's template with demo transcript for onboarding
    """
    try:
        logger.info(f"Generating demo content with template {template_id} for onboarding")
        
        # Get the template and verify access
        template = await template_service.get_template(
            template_id, auth.user.id, auth.access_token
        )
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template {template_id} not found"
            )
        
        
        # Get demo transcript
        demo_data = await get_demo_transcript()
        demo_transcript = demo_data["transcript"]
        
        # Generate content using template
        generation_result = await content_service.generate_content_with_template(
            full_transcript=demo_transcript,
            template=template,
            custom_instructions="This is for onboarding demonstration purposes."
        )
        
        logger.info(f"Demo content generated successfully for template {template_id}")
        
        # Return response without saving to database (it's just a demo)
        return ContentGenerationResponse(
            id=template_id,  # Use template ID as placeholder
            content=generation_result["content"],
            metadata={
                **generation_result["content_metadata"],
                "demo_mode": True,
                "demo_transcript_title": demo_data["title"]
            },
            generation_cost_cents=generation_result["generation_cost_cents"],
            generation_duration_ms=generation_result["generation_duration_ms"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error generating demo content: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate demo content: {str(e)}"
        ) 
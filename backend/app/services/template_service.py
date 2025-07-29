from typing import Optional, List, Dict, Any
from uuid import UUID
import logging
from datetime import datetime
from app.services.supabase_service import supabase_service, DatabaseError, NotFoundError, ValidationError
from app.models.schemas import (
    ContentTemplate, ContentTemplateCreate, ContentTemplateUpdate,
    GeneratedContentModel, GeneratedContentCreate, GeneratedContentUpdate,
    TemplateStatus
)

logger = logging.getLogger(__name__)

class TemplateServiceError(Exception):
    """Base exception for TemplateService errors"""
    pass

class TemplateService:
    """Service for managing content templates and generated content"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    # Content Template CRUD Operations
    
    async def create_template(
        self, 
        template: ContentTemplateCreate, 
        user_id: UUID,
        access_token: str,
        refresh_token: str = None
    ) -> ContentTemplate:
        """Create a new content template"""
        try:
            # Validate that user belongs to the client
            user_client = await supabase_service.get_user_client(user_id)
            if not user_client or user_client.id != template.client_id:
                raise ValidationError("User does not belong to the specified client")
            
            # Check for duplicate template names within client
            existing = await self.get_template_by_name(template.client_id, template.name, access_token, refresh_token)
            if existing:
                raise ValidationError(f"Template with name '{template.name}' already exists for this organization")
            
            # Use user-authenticated client for audit trigger compatibility
            client = await supabase_service.create_user_authenticated_client(access_token, refresh_token)
            
            template_data = {
                "client_id": str(template.client_id),
                "name": template.name,
                "description": template.description,
                "content_type_name": template.content_type_name,
                "structured_prompt": template.structured_prompt,
                "example_content": template.example_content,
                "status": template.status.value,
                "model_settings": template.model_settings
                # Audit fields handled automatically by database triggers
            }
            
            response = await client.table('content_templates').insert(template_data).execute()
            
            if not response.data:
                raise DatabaseError("Failed to create content template")
            
            return ContentTemplate(**response.data[0])
            
        except Exception as e:
            self.logger.error(f"Error creating content template: {str(e)}", exc_info=True)
            raise TemplateServiceError(f"Failed to create template: {str(e)}") from e
    
    async def get_template(self, template_id: UUID, user_id: UUID, access_token: str, refresh_token: str = None) -> Optional[ContentTemplate]:
        """Get a content template by ID"""
        try:
            client = await supabase_service.create_user_authenticated_client(access_token, refresh_token)
            
            # Get user's client to ensure access control
            user_client = await supabase_service.get_user_client(user_id)
            if not user_client:
                raise ValidationError("User does not belong to any client")
            
            response = await client.table('content_templates')\
                .select("*")\
                .eq("id", str(template_id))\
                .eq("client_id", str(user_client.id))\
                .is_("deleted_at", "null")\
                .single()\
                .execute()
            
            if not response.data:
                return None
            
            return ContentTemplate(**response.data)
            
        except Exception as e:
            self.logger.error(f"Error getting content template {template_id}: {str(e)}", exc_info=True)
            raise TemplateServiceError(f"Failed to get template: {str(e)}") from e
    
    async def get_template_by_name(
        self, 
        client_id: UUID, 
        name: str,
        access_token: str,
        refresh_token: str = None
    ) -> Optional[ContentTemplate]:
        """Get a content template by name within a client"""
        try:
            client = await supabase_service.create_user_authenticated_client(access_token, refresh_token)
            
            response = await client.table('content_templates')\
                .select("*")\
                .eq("client_id", str(client_id))\
                .eq("name", name)\
                .eq("status", "active")\
                .is_("deleted_at", "null")\
                .single()\
                .execute()
            
            if not response.data:
                return None
            
            return ContentTemplate(**response.data)
            
        except Exception as e:
            if "PGRST116" in str(e):  # No rows found
                return None
            self.logger.error(f"Error getting template by name: {str(e)}", exc_info=True)
            raise TemplateServiceError(f"Failed to get template by name: {str(e)}") from e
    
    async def list_templates(
        self, 
        user_id: UUID,
        access_token: str,
        refresh_token: str = None,
        status: Optional[TemplateStatus] = None,
        content_type_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List all content templates for user's client"""
        try:
            client = await supabase_service.create_user_authenticated_client(access_token, refresh_token)
            
            # Get user's client
            user_client = await supabase_service.get_user_client(user_id)
            if not user_client:
                raise ValidationError("User does not belong to any client")
            
            query = client.table('content_templates_with_creator')\
                .select("*")\
                .eq("client_id", str(user_client.id))\
                .order("created_at", desc=True)
            
            # Apply filters
            if status:
                query = query.eq("status", status.value)
            
            if content_type_name:
                query = query.eq("content_type_name", content_type_name)
            
            response = await query.execute()
            
            # Return raw dict data to preserve all fields from view
            return response.data
            
        except Exception as e:
            self.logger.error(f"Error listing content templates: {str(e)}", exc_info=True)
            raise TemplateServiceError(f"Failed to list templates: {str(e)}") from e
    
    async def update_template(
        self, 
        template_id: UUID, 
        updates: ContentTemplateUpdate, 
        user_id: UUID,
        access_token: str,
        refresh_token: str = None
    ) -> ContentTemplate:
        """Update a content template"""
        try:
            # First verify the template exists and user has access
            existing_template = await self.get_template(template_id, user_id, access_token, refresh_token)
            if not existing_template:
                raise NotFoundError(f"Template {template_id} not found")
            
            client = await supabase_service.create_user_authenticated_client(access_token, refresh_token)
            
            # Build update data (only include non-None fields)
            # Audit fields handled automatically by database triggers
            update_data = {}
            
            if updates.name is not None:
                # Check for name conflicts
                existing_by_name = await self.get_template_by_name(existing_template.client_id, updates.name, access_token, refresh_token)
                if existing_by_name and existing_by_name.id != template_id:
                    raise ValidationError(f"Template with name '{updates.name}' already exists")
                update_data["name"] = updates.name
            
            if updates.description is not None:
                update_data["description"] = updates.description
            
            if updates.structured_prompt is not None:
                update_data["structured_prompt"] = updates.structured_prompt
            
            if updates.example_content is not None:
                # Check if examples actually changed
                current_examples = existing_template.example_content or []
                new_examples = updates.example_content
                
                if current_examples != new_examples:
                    # Examples changed - need to regenerate structured prompt
                    from app.services.pattern_extraction_service import pattern_extraction_service, PatternExtractionError
                    
                    try:
                        # Extract patterns from new examples
                        analysis_result = await pattern_extraction_service.extract_patterns(
                            examples=new_examples,
                            content_type_name=existing_template.content_type_name,
                            description=existing_template.description
                        )
                        
                        # Generate new structured prompt
                        new_structured_prompt = await pattern_extraction_service.generate_structured_prompt(analysis_result)
                        
                        # Validate confidence threshold
                        from app.config.settings import settings
                        min_confidence = getattr(settings, 'PATTERN_CONFIDENCE_THRESHOLD', 0.7)
                        if analysis_result.confidence_score < min_confidence:
                            raise ValidationError(
                                f"Pattern extraction confidence too low ({analysis_result.confidence_score:.2f}). "
                                f"Please provide more consistent examples."
                            )
                        
                        # Update both examples and structured prompt
                        update_data["example_content"] = new_examples
                        update_data["structured_prompt"] = new_structured_prompt
                        
                        self.logger.info(
                            f"Regenerated structured prompt for template {template_id}: "
                            f"confidence={analysis_result.confidence_score:.3f}"
                        )
                        
                    except PatternExtractionError as e:
                        raise ValidationError(f"Failed to regenerate template from examples: {str(e)}")
                else:
                    # Examples unchanged - just update the field
                    update_data["example_content"] = updates.example_content
            
            if updates.status is not None:
                update_data["status"] = updates.status.value
            
            if updates.model_settings is not None:
                update_data["model_settings"] = updates.model_settings
            
            response = await client.table('content_templates')\
                .update(update_data)\
                .eq("id", str(template_id))\
                .execute()
            
            if not response.data:
                raise DatabaseError("Failed to update content template")
            
            return ContentTemplate(**response.data[0])
            
        except Exception as e:
            self.logger.error(f"Error updating content template {template_id}: {str(e)}", exc_info=True)
            raise TemplateServiceError(f"Failed to update template: {str(e)}") from e
    
    async def delete_template(self, template_id: UUID, user_id: UUID, access_token: str, refresh_token: str = None) -> bool:
        """Soft delete a content template"""
        try:
            # Verify template exists and user has access
            existing_template = await self.get_template(template_id, user_id, access_token, refresh_token)
            if not existing_template:
                raise NotFoundError(f"Template {template_id} not found")
            
            client = await supabase_service.create_user_authenticated_client(access_token, refresh_token)
            
            # Soft delete by setting deleted_at timestamp
            # Audit fields handled automatically by database triggers
            response = await client.table('content_templates')\
                .update({
                    "deleted_at": datetime.utcnow().isoformat()
                })\
                .eq("id", str(template_id))\
                .execute()
            
            return len(response.data) > 0
            
        except Exception as e:
            self.logger.error(f"Error deleting content template {template_id}: {str(e)}", exc_info=True)
            raise TemplateServiceError(f"Failed to delete template: {str(e)}") from e
    
    # Generated Content CRUD Operations
    
    async def create_generated_content(
        self, 
        content: GeneratedContentCreate, 
        user_id: UUID,
        access_token: str,
        refresh_token: str = None
    ) -> GeneratedContentModel:
        """Create a new generated content record"""
        try:
            # Verify user has access to the client
            user_client = await supabase_service.get_user_client(user_id)
            if not user_client or user_client.id != content.client_id:
                raise ValidationError("User does not belong to the specified client")
            
            # Verify template belongs to same client
            template = await self.get_template(content.template_id, user_id, access_token, refresh_token)
            if not template:
                raise ValidationError("Template not found or access denied")
            
            client = await supabase_service.create_user_authenticated_client(access_token, refresh_token)
            
            content_data = {
                "client_id": str(content.client_id),
                "transcript_id": str(content.transcript_id),
                "template_id": str(content.template_id),
                "content": content.content,
                "content_metadata": content.content_metadata,
                "generation_settings": content.generation_settings,
                "generation_cost_cents": content.generation_cost_cents,
                "generation_duration_ms": content.generation_duration_ms,
                "user_edits_count": content.user_edits_count,
                "last_edited_at": content.last_edited_at.isoformat() if content.last_edited_at else None
                # Audit fields handled automatically by database triggers
            }
            
            response = await client.table('generated_content').insert(content_data).execute()
            
            if not response.data:
                raise DatabaseError("Failed to create generated content")
            
            return GeneratedContentModel(**response.data[0])
            
        except Exception as e:
            self.logger.error(f"Error creating generated content: {str(e)}", exc_info=True)
            raise TemplateServiceError(f"Failed to create generated content: {str(e)}") from e
    
    async def get_generated_content(
        self, 
        content_id: UUID, 
        user_id: UUID,
        access_token: str,
        refresh_token: str = None
    ) -> Optional[GeneratedContentModel]:
        """Get generated content by ID"""
        try:
            client = await supabase_service.create_user_authenticated_client(access_token, refresh_token)
            
            # Get user's client for access control
            user_client = await supabase_service.get_user_client(user_id)
            if not user_client:
                raise ValidationError("User does not belong to any client")
            
            response = await client.table('generated_content')\
                .select("*")\
                .eq("id", str(content_id))\
                .eq("client_id", str(user_client.id))\
                .is_("deleted_at", "null")\
                .single()\
                .execute()
            
            if not response.data:
                return None
            
            return GeneratedContentModel(**response.data)
            
        except Exception as e:
            self.logger.error(f"Error getting generated content {content_id}: {str(e)}", exc_info=True)
            raise TemplateServiceError(f"Failed to get generated content: {str(e)}") from e
    
    async def list_generated_content_by_transcript(
        self, 
        transcript_id: UUID, 
        user_id: UUID,
        access_token: str,
        refresh_token: str = None
    ) -> List[GeneratedContentModel]:
        """List all generated content for a specific transcript"""
        try:
            client = await supabase_service.create_user_authenticated_client(access_token, refresh_token)
            
            # Get user's client for access control
            user_client = await supabase_service.get_user_client(user_id)
            if not user_client:
                raise ValidationError("User does not belong to any client")
            
            response = await client.table('generated_content')\
                .select("*")\
                .eq("transcript_id", str(transcript_id))\
                .eq("client_id", str(user_client.id))\
                .is_("deleted_at", "null")\
                .order("created_at", desc=True)\
                .execute()
            
            return [GeneratedContentModel(**content) for content in response.data]
            
        except Exception as e:
            self.logger.error(f"Error listing generated content for transcript {transcript_id}: {str(e)}", exc_info=True)
            raise TemplateServiceError(f"Failed to list generated content: {str(e)}") from e

# Create singleton instance
template_service = TemplateService()
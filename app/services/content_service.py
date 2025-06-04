import logging
import json
from typing import Dict, List, Any
import openai
from openai.types.chat import ChatCompletion
from app.config.settings import settings
from app.models.schemas import SegmentType, Segment, ContentType, GeneratedContent

logger = logging.getLogger(__name__)

class ContentService:
    """Service for generating content from sermon segments using OpenAI"""
    
    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        
    async def generate_content(
        self,
        segments: List[Segment],
        content_type: ContentType
    ) -> GeneratedContent:
        """
        Generate content from sermon segments
        
        Args:
            segments: List of sermon segments
            content_type: Type of content to generate
            
        Returns:
            Generated content object
        """
        try:
            # Combine relevant segments
            combined_text = self._combine_segments(segments)
            
            # Get appropriate prompt based on content type
            prompt = self._get_prompt_for_type(content_type)
            
            # Generate content
            response: ChatCompletion = self.client.chat.completions.create(
                model=settings.DEFAULT_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at creating engaging church content."
                    },
                    {
                        "role": "user",
                        "content": prompt.format(text=combined_text)
                    }
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            content = json.loads(response.choices[0].message.content)
            
            return GeneratedContent(
                type=content_type,
                content=content["content"],
                metadata=content.get("metadata", {})
            )
            
        except Exception as e:
            logger.error(
                f"Error generating {content_type} content: {str(e)}",
                exc_info=True
            )
            raise
            
    def _combine_segments(self, segments: List[Segment]) -> str:
        """Combine segments into a single text, filtering by relevance"""
        relevant_segments = [
            s for s in segments 
            if s.type in [SegmentType.sermon, SegmentType.prayer]
        ]
        return " ".join(s.text for s in relevant_segments)
        
    def _get_prompt_for_type(self, content_type: ContentType) -> str:
        """Get the appropriate prompt template for the content type"""
        prompts = {
            ContentType.devotional: settings.DEVOTIONAL_PROMPT,
            ContentType.summary: settings.SUMMARY_PROMPT,
            ContentType.discussion: settings.DISCUSSION_PROMPT,
            ContentType.whats_on: settings.WHATS_ON_PROMPT
        }
        return prompts[content_type]

content_service = ContentService() 
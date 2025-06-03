import logging
import json
from typing import Dict, Any
import openai
from app.config.settings import settings
from app.models.schemas import SegmentType

logger = logging.getLogger(__name__)

class OpenAIService:
    """Service for handling OpenAI operations"""
    
    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
    
    async def classify_segment(self, text: str) -> Dict[str, Any]:
        """
        Classify a segment of text using GPT-4
        
        Args:
            text: The text to classify
            
        Returns:
            Dict containing the classification type and confidence
        """
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing church service transcripts."},
                    {"role": "user", "content": settings.SEGMENT_CLASSIFIER_PROMPT.format(text=text)}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            classification = response.choices[0].message.content
            classification_data = json.loads(classification)
            
            return {
                "type": SegmentType(classification_data["type"].lower()),
                "confidence": classification_data["confidence"]
            }
            
        except Exception as e:
            logger.error(f"Error in OpenAI classification: {str(e)}")
            raise

openai_service = OpenAIService() 
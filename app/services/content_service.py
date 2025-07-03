import logging
import json
import time
from typing import Dict, List, Any
import openai
from openai.types.chat import ChatCompletion
from app.config.settings import settings
from app.models.schemas import ContentTemplate

logger = logging.getLogger(__name__)

class ContentService:
    """Service for generating content from sermon segments using OpenAI"""
    
    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        self.logger = logging.getLogger(__name__)
        
    
    async def generate_content_with_template(
        self,
        full_transcript: str,
        template: ContentTemplate,
        custom_instructions: str = None
    ) -> Dict[str, Any]:
        """
        Generate content using a custom template
        
        Args:
            full_transcript: Complete sermon transcript text
            template: Content template to use for generation
            custom_instructions: Optional additional instructions
            
        Returns:
            Dictionary with generated content and metadata
        """
        try:
            start_time = time.time()
            
            # Debug logging
            self.logger.info(f"Template ID: {template.id}")
            self.logger.info(f"Template has structured_prompt: {hasattr(template, 'structured_prompt')}")
            if hasattr(template, 'structured_prompt'):
                self.logger.info(f"Structured prompt length: {len(template.structured_prompt)}")
                self.logger.info(f"Structured prompt preview: {template.structured_prompt[:200]}...")
            
            # Build the prompt with template and full transcript
            if not hasattr(template, 'structured_prompt') or not template.structured_prompt:
                self.logger.error(f"Template {template.id} missing structured_prompt field")
                raise ValueError(f"Template {template.id} is missing the structured_prompt field")
            
            base_prompt = template.structured_prompt.format(text=full_transcript)
            
            # Add custom instructions if provided
            if custom_instructions:
                base_prompt += f"\n\nAdditional Instructions:\n{custom_instructions}"
            
            # Use template's model settings
            model_settings = template.model_settings
            model = model_settings.get("model", settings.DEFAULT_MODEL)
            temperature = model_settings.get("temperature", 0.7)
            max_tokens = model_settings.get("max_tokens", 2000)
            
            # Generate content
            response: ChatCompletion = self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert content creator who specializes in generating "
                            "church content that matches specific organizational styles and preferences. "
                            "Follow the provided template guidelines precisely to maintain consistency "
                            "with the organization's voice and format. "
                            "Please respond with a JSON object containing the generated content."
                        )
                    },
                    {
                        "role": "user",
                        "content": base_prompt
                    }
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={"type": "json_object"}
            )
            
            generation_time_ms = int((time.time() - start_time) * 1000)
            
            # Parse response
            content_data = json.loads(response.choices[0].message.content)
            
            # Calculate approximate cost (rough estimate based on tokens)
            input_tokens = len(base_prompt.split()) * 1.3  # Rough estimate
            output_tokens = len(str(content_data).split()) * 1.3
            
            # Rough cost calculation for GPT-4 (adjust as needed)
            cost_per_1k_input = 0.03 if "gpt-4" in model else 0.002
            cost_per_1k_output = 0.06 if "gpt-4" in model else 0.002
            
            estimated_cost_cents = int(
                (input_tokens / 1000 * cost_per_1k_input + 
                 output_tokens / 1000 * cost_per_1k_output) * 100
            )
            
            return {
                "content": content_data.get("content", str(content_data)),
                "content_metadata": {
                    "model_used": model,
                    "template_id": str(template.id),
                    "template_name": template.name,
                    "content_type": template.content_type_name,
                    "transcript_length": len(full_transcript),
                    "custom_instructions_provided": bool(custom_instructions)
                },
                "generation_settings": {
                    "model": model,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                },
                "generation_cost_cents": estimated_cost_cents,
                "generation_duration_ms": generation_time_ms
            }
            
        except Exception as e:
            self.logger.error(
                f"Error generating content with template {template.id}: {str(e)}",
                exc_info=True
            )
            raise
    
    def extract_full_transcript_from_deepgram(self, deepgram_response: Dict[str, Any]) -> str:
        """
        Extract the full transcript text from Deepgram response
        
        Args:
            deepgram_response: Raw Deepgram API response
            
        Returns:
            Full transcript as a single string
        """
        try:
            if 'results' not in deepgram_response or 'channels' not in deepgram_response['results']:
                raise ValueError("Invalid Deepgram response structure")
            
            channels = deepgram_response['results']['channels']
            if not channels or not channels[0].get('alternatives'):
                raise ValueError("No transcript data found in Deepgram response")
            
            # Get the first alternative (highest confidence)
            transcript = channels[0]['alternatives'][0].get('transcript', '')
            if not transcript.strip():
                raise ValueError("Empty transcript received from Deepgram")
            
            return transcript.strip()
            
        except Exception as e:
            self.logger.error(f"Error extracting transcript from Deepgram response: {str(e)}")
            raise ValueError(f"Failed to extract transcript: {str(e)}") from e

content_service = ContentService() 
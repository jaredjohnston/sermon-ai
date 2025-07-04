import logging
import json
from typing import Dict, List, Any
import openai
from openai.types.chat import ChatCompletion
from app.config.settings import settings
from app.models.schemas import SegmentType, Segment

logger = logging.getLogger(__name__)

class ClassifierService:
    """Service for classifying sermon segments using OpenAI"""
    
    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        self.CHUNK_DURATION = 120.0  # 2 minutes in seconds
    
    async def classify_segments(
        self,
        utterances: List[Dict[str, Any]]
    ) -> List[Segment]:
        """
        Classify a list of utterances into sermon segments, combining them into 2-minute chunks
        
        Args:
            utterances: List of utterances from Deepgram
            
        Returns:
            List of classified segments
        """
        # Sort utterances by start time to ensure proper sequencing
        sorted_utterances = sorted(utterances, key=lambda x: x["start"])
        chunks = []
        current_chunk = {
            "texts": [],
            "start": None,
            "end": None
        }
        
        # Group utterances into 2-minute chunks
        for utterance in sorted_utterances:
            if current_chunk["start"] is None:
                current_chunk["start"] = utterance["start"]
            
            # If this utterance would make the chunk too long, finalize current chunk
            if (utterance["end"] - current_chunk["start"]) > self.CHUNK_DURATION:
                current_chunk["end"] = utterance["end"]
                chunks.append(current_chunk)
                # Start new chunk with current utterance
                current_chunk = {
                    "texts": [utterance["transcript"]],
                    "start": utterance["start"],
                    "end": utterance["end"]
                }
            else:
                # Add to current chunk
                current_chunk["texts"].append(utterance["transcript"])
                current_chunk["end"] = utterance["end"]
        
        # Don't forget the last chunk
        if current_chunk["texts"]:
            chunks.append(current_chunk)
        
        classified_segments = []
        
        # Classify each chunk
        for chunk in chunks:
            try:
                # Combine all texts in the chunk
                combined_text = " ".join(chunk["texts"])
                
                # Get classification for the chunk
                classification = await self._classify_text(
                    text=combined_text
                )
                
                # Create segment
                segment = Segment(
                    type=classification["type"],
                    text=combined_text,
                    start_time=chunk["start"],
                    end_time=chunk["end"],
                    confidence=classification["confidence"]
                )
                
                classified_segments.append(segment)
                logger.info(
                    f"Classified chunk as {segment.type} "
                    f"with confidence {segment.confidence} "
                    f"(duration: {segment.end_time - segment.start_time:.1f}s)"
                )
                
            except Exception as e:
                logger.error(
                    f"Error classifying chunk: {str(e)}",
                    exc_info=True
                )
                continue
        
        return classified_segments
    
    async def _classify_text(
        self,
        text: str
    ) -> Dict[str, Any]:
        """
        Classify a single piece of text using GPT-4
        
        Args:
            text: The text to classify
            
        Returns:
            Dictionary containing classification type and confidence
        """
        try:
            response: ChatCompletion = self.client.chat.completions.create(
                model=settings.DEFAULT_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at analyzing church service transcripts."
                    },
                    {
                        "role": "user",
                        "content": settings.SEGMENT_CLASSIFIER_PROMPT.format(text=text)
                    }
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            classification = json.loads(response.choices[0].message.content)
            
            return {
                "type": SegmentType(classification["type"].lower()),
                "confidence": classification["confidence"]
            }
            
        except Exception as e:
            logger.error(f"Error in GPT classification: {str(e)}")
            raise

classifier_service = ClassifierService() 
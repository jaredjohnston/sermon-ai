import logging
import json
import time
from typing import Dict, List, Any, Optional
from collections import defaultdict
from openai import AsyncOpenAI
from app.config.settings import settings
from app.models.schemas import SpeakerCategory, SpeakerClassification, SpeakerClassificationResult

logger = logging.getLogger(__name__)

class SpeakerClassificationService:
    """AI-powered speaker classification service for sermon transcripts"""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
    def _extract_speaker_samples(self, utterances: List[Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
        """
        Extract the first 150 words for each speaker from utterances
        
        Args:
            utterances: List of utterances from Deepgram with speaker diarization
            
        Returns:
            Dict mapping speaker_id to sample data including text and word count
        """
        if not utterances:
            raise ValueError("No utterances provided")
            
        # Sort utterances by start time to ensure proper sequencing
        sorted_utterances = sorted(utterances, key=lambda x: x.get("start", 0))
        
        # Group utterances by speaker
        speaker_utterances = defaultdict(list)
        for utterance in sorted_utterances:
            speaker_id = utterance.get("speaker")
            if speaker_id is not None:
                speaker_utterances[speaker_id].append(utterance)
        
        # Extract first 150 words per speaker
        speaker_samples = {}
        for speaker_id, speaker_utts in speaker_utterances.items():
            words = []
            total_words = 0
            
            for utterance in speaker_utts:
                text = utterance.get("transcript", "").strip()
                if text:
                    utterance_words = text.split()
                    remaining_words = 150 - total_words
                    
                    if remaining_words <= 0:
                        break
                        
                    words.extend(utterance_words[:remaining_words])
                    total_words += len(utterance_words[:remaining_words])
                    
                    if total_words >= 150:
                        break
            
            if words:
                speaker_samples[speaker_id] = {
                    "sample_text": " ".join(words),
                    "word_count": len(words),
                    "total_utterances": len(speaker_utts),
                    "total_words": sum(len(u.get("transcript", "").split()) for u in speaker_utts)
                }
        
        return speaker_samples
    
    async def classify_speakers(self, utterances: List[Dict[str, Any]]) -> SpeakerClassificationResult:
        """
        Classify speakers in sermon transcript using OpenAI GPT
        
        Args:
            utterances: List of utterances from Deepgram with speaker diarization
            
        Returns:
            SpeakerClassificationResult with classifications for each speaker
        """
        start_time = time.time()
        
        try:
            # Extract speaker samples
            speaker_samples = self._extract_speaker_samples(utterances)
            
            if not speaker_samples:
                raise ValueError("No speaker samples found")
            
            # Prepare the classification prompt
            prompt = self._build_classification_prompt(speaker_samples)
            
            # Call OpenAI API
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert at analyzing church service transcripts. Your task is to classify speakers based on their content, not their position in the service. 

Categories:
- opening_words: Opening prayers, welcome messages, introductory remarks, welcoming new visitors and first-time guests, connecting with newcomers ("Welcome to our church family", "We're glad you're here", "If this is your first time visiting", "New to our church")
- worship: Worship leading, singing instructions, music-related content including: song lyrics, hymn verses, repetitive chorus and verse structures, worship song titles, singing directions ("Please stand and join us in singing", "Let's worship together", "Turn to hymn number", "Raise your hands in praise"), musical instructions, repeated refrains, call-and-response patterns, and any content with lyrical or poetic structure typical of worship songs
- sermon: Main teaching content, biblical exposition, pastoral messages
- automated_announcements: Automated systems, recorded messages, robotic announcements including pre-service instructions ("Please take your seats", "The service will begin in 5 minutes", "Please silence your mobile devices", "Welcome to [Church Name]"), typically with consistent, formal tone and repetitive messaging
- announcements: Live announcements about events, news, administrative items
- giving_offering: Content related to tithes, offerings, financial stewardship
- closing_words: Closing prayers, benedictions, final remarks
- other: Any content that doesn't fit the above categories

IMPORTANT: Only classify speakers based on what is actually present in their content. Do not force or invent categories that don't exist in the transcript. If a transcript only contains sermon content, only classify it as sermon. If there's no worship content, don't assign any speaker to the worship category. Be accurate to what's actually said, not what you expect to be in a church service.

Return a JSON object with a "speakers" array containing objects with "speaker_id", "category", and "confidence" fields. Confidence should be between 0.0 and 1.0.

Example response format:
{
  "speakers": [
    {
      "speaker_id": 0,
      "category": "opening_words",
      "confidence": 0.95
    },
    {
      "speaker_id": 1,
      "category": "worship",
      "confidence": 0.90
    },
    {
      "speaker_id": 2,
      "category": "sermon",
      "confidence": 0.98
    }
  ]
}"""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            # Parse the response
            response_text = response.choices[0].message.content
            classification_data = json.loads(response_text)
            
            # Build the result
            speakers = []
            for speaker_data in classification_data.get("speakers", []):
                speaker_id = speaker_data["speaker_id"]
                category = SpeakerCategory(speaker_data["category"])
                confidence = speaker_data["confidence"]
                
                if speaker_id in speaker_samples:
                    sample_data = speaker_samples[speaker_id]
                    speakers.append(SpeakerClassification(
                        speaker_id=speaker_id,
                        category=category,
                        confidence=confidence,
                        word_count=sample_data["word_count"],
                        sample_text=sample_data["sample_text"]  # Store full 150-word sample
                    ))
            
            processing_time = int((time.time() - start_time) * 1000)
            
            return SpeakerClassificationResult(
                speakers=speakers,
                metadata={
                    "total_speakers": len(speaker_samples),
                    "model_used": "gpt-4o",
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0
                },
                processing_time_ms=processing_time,
                api_cost_cents=self._calculate_api_cost(response.usage) if response.usage else 0
            )
            
        except Exception as e:
            logger.error(f"Error in speaker classification: {str(e)}")
            raise
    
    def _build_classification_prompt(self, speaker_samples: Dict[int, Dict[str, Any]]) -> str:
        """Build the classification prompt for OpenAI"""
        prompt_parts = [
            "Please classify each speaker in this church service transcript based on their content:",
            ""
        ]
        
        for speaker_id, sample_data in speaker_samples.items():
            prompt_parts.append(f"Speaker {speaker_id} ({sample_data['word_count']} words sampled, {sample_data['total_words']} total words):")
            prompt_parts.append(f'"{sample_data["sample_text"]}"')
            prompt_parts.append("")
        
        prompt_parts.append("Classify each speaker into one of the defined categories and provide a confidence score.")
        
        return "\n".join(prompt_parts)
    
    def _calculate_api_cost(self, usage) -> int:
        """Calculate API cost in cents based on token usage"""
        if not usage:
            return 0
        
        # GPT-4o pricing (approximate)
        prompt_cost_per_1k = 0.005  # $0.005 per 1K prompt tokens
        completion_cost_per_1k = 0.015  # $0.015 per 1K completion tokens
        
        prompt_cost = (usage.prompt_tokens / 1000) * prompt_cost_per_1k
        completion_cost = (usage.completion_tokens / 1000) * completion_cost_per_1k
        
        total_cost_dollars = prompt_cost + completion_cost
        return int(total_cost_dollars * 100)  # Convert to cents
    
    def filter_content_by_category(
        self, 
        utterances: List[Dict[str, Any]], 
        classification_result: SpeakerClassificationResult,
        include_categories: List[SpeakerCategory] = None,
        exclude_categories: List[SpeakerCategory] = None
    ) -> Dict[str, Any]:
        """
        Filter transcript content based on speaker classifications
        
        Args:
            utterances: Original utterances from Deepgram
            classification_result: Speaker classification results
            include_categories: Categories to include (if None, includes all except excluded)
            exclude_categories: Categories to exclude (default: automated_announcements)
            
        Returns:
            Filtered content with metadata
        """
        if exclude_categories is None:
            exclude_categories = [SpeakerCategory.automated_announcements]
            
        # Create speaker category mapping
        speaker_categories = {
            speaker.speaker_id: speaker.category 
            for speaker in classification_result.speakers
        }
        
        # Filter utterances
        filtered_utterances = []
        for utterance in utterances:
            speaker_id = utterance.get("speaker")
            category = speaker_categories.get(speaker_id, SpeakerCategory.other)
            
            # Apply include/exclude filters
            if include_categories and category not in include_categories:
                continue
            if exclude_categories and category in exclude_categories:
                continue
                
            filtered_utterances.append({
                **utterance,
                "speaker_category": category.value
            })
        
        # Sort by start time to maintain chronological order
        filtered_utterances.sort(key=lambda x: x.get("start", 0))
        
        # Generate combined text
        combined_text = " ".join([
            utterance.get("transcript", "").strip()
            for utterance in filtered_utterances
        ])
        
        # Calculate statistics
        total_duration = sum(
            utterance.get("end", 0) - utterance.get("start", 0)
            for utterance in filtered_utterances
        )
        
        # Category breakdown
        category_stats = defaultdict(lambda: {"utterances": 0, "words": 0, "duration": 0})
        for utterance in filtered_utterances:
            category = utterance.get("speaker_category", "other")
            text = utterance.get("transcript", "")
            duration = utterance.get("end", 0) - utterance.get("start", 0)
            
            category_stats[category]["utterances"] += 1
            category_stats[category]["words"] += len(text.split())
            category_stats[category]["duration"] += duration
        
        return {
            "filtered_text": combined_text,
            "filtered_utterances": filtered_utterances,
            "word_count": len(combined_text.split()),
            "utterance_count": len(filtered_utterances),
            "total_duration": total_duration,
            "category_breakdown": dict(category_stats),
            "filters_applied": {
                "include_categories": [cat.value for cat in include_categories] if include_categories else None,
                "exclude_categories": [cat.value for cat in exclude_categories] if exclude_categories else None
            }
        }

# Export singleton instance
speaker_classification_service = SpeakerClassificationService()
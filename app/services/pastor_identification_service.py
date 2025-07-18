import logging
from typing import Dict, List, Any, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)

class PastorIdentificationService:
    """Service for identifying pastor content in church service transcripts using simple structure-based algorithm"""
    
    def __init__(self):
        pass
        
    def identify_pastor_from_utterances(self, utterances: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Phase 1: Pastor Identification Function
        
        Algorithm:
        1. Count words and speaking time for each speaker
        2. Identify the first speaker (worship leader)
        3. Exclude the worship speaker
        4. Find the speaker with the most words
        
        Args:
            utterances: List of utterances from Deepgram with speaker diarization
            
        Returns:
            Dict containing:
                - pastor_speaker_id: ID of the identified pastor speaker
                - worship_speaker_id: ID of the excluded first speaker (worship leader)
                - speaker_stats: Statistics about all speakers
        """
        if not utterances:
            raise ValueError("No utterances provided for pastor identification")
            
        # Sort utterances by start time to ensure proper sequencing
        sorted_utterances = sorted(utterances, key=lambda x: x.get("start", 0))
        
        # Count words and speaking time for each speaker
        speaker_stats = self._calculate_speaker_stats(sorted_utterances)
        
        if not speaker_stats:
            raise ValueError("No speaker data found in utterances")
            
        # Identify the first speaker (worship leader)
        worship_speaker_id = sorted_utterances[0].get("speaker")
        
        # Exclude the worship speaker
        remaining_speakers = {
            speaker_id: stats for speaker_id, stats in speaker_stats.items() 
            if speaker_id != worship_speaker_id
        }
        
        if not remaining_speakers:
            raise ValueError("No speakers found after excluding worship leader")
            
        # Find the speaker with the most words
        pastor_speaker_id = max(remaining_speakers.keys(), 
                              key=lambda x: remaining_speakers[x]["word_count"])
        
        logger.info(f"Identified pastor as speaker {pastor_speaker_id} with {speaker_stats[pastor_speaker_id]['word_count']} words")
        logger.info(f"Excluded worship leader {worship_speaker_id} with {speaker_stats[worship_speaker_id]['word_count']} words")
        
        return {
            "pastor_speaker_id": pastor_speaker_id,
            "worship_speaker_id": worship_speaker_id,
            "speaker_stats": speaker_stats
        }
        
    def extract_pastor_content(self, utterances: List[Dict[str, Any]], worship_speaker_id: int) -> Dict[str, Any]:
        """
        Phase 2: Content Extraction
        
        Algorithm:
        1. Extract all words from ALL speakers except the worship leader (speaker 0)
        2. Create full text from all pastoral speakers (main pastor, junior pastors, announcement speakers, etc.)
        3. Calculate total duration and word count for all pastoral content
        
        Args:
            utterances: List of utterances from Deepgram
            worship_speaker_id: ID of the worship leader to exclude (typically speaker 0)
            
        Returns:
            Dict containing:
                - pastor_text: Full text from all non-worship speakers
                - word_count: Total word count
                - duration: Total speaking duration
                - utterance_count: Number of pastoral utterances
                - speaker_breakdown: Statistics per non-worship speaker
        """
        if not utterances:
            raise ValueError("No utterances provided for content extraction")
            
        # Extract all words from ALL speakers except the worship leader
        non_worship_utterances = [
            utterance for utterance in utterances
            if utterance.get("speaker") != worship_speaker_id
        ]
        
        if not non_worship_utterances:
            raise ValueError(f"No non-worship utterances found after excluding worship speaker {worship_speaker_id}")
        
        # Create full text from all pastoral speakers' words
        pastor_text = " ".join([
            utterance.get("transcript", "").strip()
            for utterance in non_worship_utterances
        ])
        
        # Calculate total duration and word count for all pastoral content
        total_duration = sum(
            utterance.get("end", 0) - utterance.get("start", 0)
            for utterance in non_worship_utterances
        )
        
        word_count = len(pastor_text.split())
        utterance_count = len(non_worship_utterances)
        
        # Create speaker breakdown for all non-worship speakers
        speaker_breakdown = {}
        for utterance in non_worship_utterances:
            speaker_id = utterance.get("speaker")
            if speaker_id not in speaker_breakdown:
                speaker_breakdown[speaker_id] = {
                    "word_count": 0,
                    "utterance_count": 0,
                    "duration": 0.0
                }
            
            text = utterance.get("transcript", "")
            duration = utterance.get("end", 0) - utterance.get("start", 0)
            
            speaker_breakdown[speaker_id]["word_count"] += len(text.split())
            speaker_breakdown[speaker_id]["utterance_count"] += 1
            speaker_breakdown[speaker_id]["duration"] += duration
        
        logger.info(f"Extracted pastoral content from {len(speaker_breakdown)} non-worship speakers: {word_count} words, {utterance_count} utterances, {total_duration:.1f}s duration")
        logger.info(f"Speaker breakdown: {speaker_breakdown}")
        
        return {
            "pastor_text": pastor_text,
            "word_count": word_count,
            "duration": total_duration,
            "utterance_count": utterance_count,
            "speaker_breakdown": speaker_breakdown
        }
        
    def _calculate_speaker_stats(self, utterances: List[Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
        """Calculate word count and speaking time for each speaker"""
        speaker_stats = defaultdict(lambda: {
            "word_count": 0,
            "utterance_count": 0,
            "total_duration": 0.0,
            "first_appearance": None,
            "last_appearance": None
        })
        
        for utterance in utterances:
            speaker_id = utterance.get("speaker")
            if speaker_id is None:
                continue
                
            text = utterance.get("transcript", "")
            start_time = utterance.get("start", 0)
            end_time = utterance.get("end", 0)
            duration = end_time - start_time
            
            stats = speaker_stats[speaker_id]
            stats["word_count"] += len(text.split())
            stats["utterance_count"] += 1
            stats["total_duration"] += duration
            
            if stats["first_appearance"] is None or start_time < stats["first_appearance"]:
                stats["first_appearance"] = start_time
            if stats["last_appearance"] is None or end_time > stats["last_appearance"]:
                stats["last_appearance"] = end_time
                
        return dict(speaker_stats)
    
    def create_processed_transcript(
        self, 
        raw_transcript: Dict[str, Any], 
        pastor_identification: Dict[str, Any],
        pastor_content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a processed transcript structure with pastor identification and content
        
        Args:
            raw_transcript: Original Deepgram transcript
            pastor_identification: Result from identify_pastor_from_utterances
            pastor_content: Result from extract_pastor_content
            
        Returns:
            Processed transcript with pastor-specific structure
        """
        try:
            processed_transcript = {
                "version": "1.0",
                "processing_metadata": {
                    "pastor_identified": True,
                    "pastor_speaker_id": pastor_identification["pastor_speaker_id"],
                    "worship_speaker_id": pastor_identification["worship_speaker_id"],
                    "processing_algorithm": "simple_structure_based",
                    "processed_at": None,  # Will be set by calling service
                    "speaker_stats": pastor_identification["speaker_stats"]
                },
                "speaker_identification": {
                    "pastor": {
                        "speaker_id": pastor_identification["pastor_speaker_id"],
                        "word_count": pastor_identification["speaker_stats"][pastor_identification["pastor_speaker_id"]]["word_count"],
                        "utterance_count": pastor_identification["speaker_stats"][pastor_identification["pastor_speaker_id"]]["utterance_count"],
                        "total_duration": pastor_identification["speaker_stats"][pastor_identification["pastor_speaker_id"]]["total_duration"]
                    },
                    "worship_leader": {
                        "speaker_id": pastor_identification["worship_speaker_id"],
                        "word_count": pastor_identification["speaker_stats"][pastor_identification["worship_speaker_id"]]["word_count"],
                        "utterance_count": pastor_identification["speaker_stats"][pastor_identification["worship_speaker_id"]]["utterance_count"],
                        "total_duration": pastor_identification["speaker_stats"][pastor_identification["worship_speaker_id"]]["total_duration"]
                    },
                    "other_speakers": {
                        speaker_id: stats for speaker_id, stats in pastor_identification["speaker_stats"].items()
                        if speaker_id not in [pastor_identification["pastor_speaker_id"], pastor_identification["worship_speaker_id"]]
                    }
                },
                "pastor_content": {
                    "full_text": pastor_content["pastor_text"],
                    "word_count": pastor_content["word_count"],
                    "duration": pastor_content["duration"],
                    "utterance_count": pastor_content["utterance_count"],
                    "speaker_breakdown": pastor_content["speaker_breakdown"]
                },
                "original_transcript": raw_transcript
            }
            
            logger.info("Successfully created processed transcript structure")
            
            return processed_transcript
            
        except Exception as e:
            logger.error(f"Error creating processed transcript: {str(e)}")
            raise

# Export singleton instance
pastor_identification_service = PastorIdentificationService()
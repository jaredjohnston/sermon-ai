import asyncio
import logging
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, UTC
from app.services.speaker_classification_service import speaker_classification_service
from app.services.supabase_service import supabase_service
from app.models.schemas import SpeakerCategory

logger = logging.getLogger(__name__)

class JobStatus(str, Enum):
    """Status of a background job"""
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"

@dataclass
class BackgroundJob:
    """Background job data structure"""
    job_id: str
    job_type: str
    payload: Dict[str, Any]
    status: JobStatus = JobStatus.pending
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(UTC)

class BackgroundJobService:
    """
    Simple in-memory background job queue service
    
    This is a basic implementation that can be upgraded to Redis/Celery later.
    Jobs are processed by background workers in separate asyncio tasks.
    """
    
    def __init__(self):
        self.job_queue: asyncio.Queue = asyncio.Queue()
        self.job_storage: Dict[str, BackgroundJob] = {}
        self.workers_running = False
        self.worker_tasks = []
        
    async def start_workers(self, num_workers: int = 2):
        """Start background worker tasks"""
        if self.workers_running:
            logger.warning("Background workers already running")
            return
            
        self.workers_running = True
        logger.info(f"Starting {num_workers} background workers")
        
        # Start worker tasks
        for i in range(num_workers):
            worker_task = asyncio.create_task(self._worker_loop(f"worker-{i}"))
            self.worker_tasks.append(worker_task)
            
    async def stop_workers(self):
        """Stop all background workers"""
        if not self.workers_running:
            return
            
        logger.info("Stopping background workers")
        self.workers_running = False
        
        # Cancel all worker tasks
        for task in self.worker_tasks:
            task.cancel()
            
        # Wait for tasks to finish
        await asyncio.gather(*self.worker_tasks, return_exceptions=True)
        self.worker_tasks.clear()
        
    async def queue_job(self, job_type: str, payload: Dict[str, Any]) -> str:
        """
        Queue a background job for processing
        
        Args:
            job_type: Type of job (e.g., 'ai_classification')
            payload: Job data (e.g., {'transcript_id': 'abc123'})
            
        Returns:
            Job ID for tracking
        """
        job_id = f"{job_type}_{int(time.time() * 1000)}"
        
        job = BackgroundJob(
            job_id=job_id,
            job_type=job_type,
            payload=payload
        )
        
        # Store job for tracking
        self.job_storage[job_id] = job
        
        # Add to queue for processing
        await self.job_queue.put(job)
        
        logger.info(f"Queued job {job_id} of type {job_type}")
        return job_id
        
    async def get_job_status(self, job_id: str) -> Optional[BackgroundJob]:
        """Get status of a background job"""
        return self.job_storage.get(job_id)
        
    async def _worker_loop(self, worker_name: str):
        """Main worker loop that processes jobs from the queue"""
        logger.info(f"Background worker {worker_name} started")
        
        while self.workers_running:
            try:
                # Get job from queue (wait up to 1 second)
                job = await asyncio.wait_for(self.job_queue.get(), timeout=1.0)
                
                logger.info(f"Worker {worker_name} processing job {job.job_id}")
                await self._process_job(job, worker_name)
                
                # Mark job as done in queue
                self.job_queue.task_done()
                
            except asyncio.TimeoutError:
                # No job available, continue loop
                continue
            except asyncio.CancelledError:
                # Worker is being stopped
                break
            except Exception as e:
                logger.error(f"Worker {worker_name} error: {str(e)}", exc_info=True)
                
        logger.info(f"Background worker {worker_name} stopped")
        
    async def _process_job(self, job: BackgroundJob, worker_name: str):
        """Process a single background job"""
        # Update job status
        job.status = JobStatus.processing
        job.started_at = datetime.now(UTC)
        
        try:
            # Route to appropriate handler based on job type
            if job.job_type == "ai_classification":
                await self._process_ai_classification(job)
            else:
                raise ValueError(f"Unknown job type: {job.job_type}")
                
            # Mark as completed
            job.status = JobStatus.completed
            job.completed_at = datetime.now(UTC)
            
            logger.info(f"Job {job.job_id} completed successfully by {worker_name}")
            
        except Exception as e:
            job.error_message = str(e)
            job.retry_count += 1
            
            if job.retry_count < job.max_retries:
                # Retry the job
                job.status = JobStatus.pending
                job.started_at = None
                await self.job_queue.put(job)
                logger.warning(f"Job {job.job_id} failed, retrying ({job.retry_count}/{job.max_retries}): {str(e)}")
            else:
                # Max retries reached, mark as failed
                job.status = JobStatus.failed
                job.completed_at = datetime.now(UTC)
                logger.error(f"Job {job.job_id} failed permanently after {job.max_retries} retries: {str(e)}")
                
    async def _process_ai_classification(self, job: BackgroundJob):
        """Process an AI classification job"""
        transcript_id = job.payload.get("transcript_id")
        if not transcript_id:
            raise ValueError("Missing transcript_id in job payload")
            
        logger.info(f"Processing AI classification for transcript {transcript_id}")
        
        # Get transcript from database
        transcript = await supabase_service.get_transcript_by_id(transcript_id)
        if not transcript:
            raise ValueError(f"Transcript {transcript_id} not found")
            
        # Check if already processed
        if transcript.processing_status == "completed":
            logger.info(f"Transcript {transcript_id} already processed, skipping")
            return
            
        # Update status to processing
        await supabase_service.update_transcript_system(
            transcript_id,
            {"processing_status": "processing"},
            transcript.created_by
        )
        
        try:
            # Extract utterances from raw transcript
            raw_transcript = transcript.raw_transcript
            if not raw_transcript or not raw_transcript.get("results"):
                raise ValueError("No raw transcript data available")
                
            results = raw_transcript.get("results", {})
            utterances = results.get("utterances", [])
            
            if not utterances:
                raise ValueError("No utterances found in transcript")
                
            # Run AI speaker classification
            classification_result = await speaker_classification_service.classify_speakers(utterances)
            
            # Filter content to exclude automated announcements, worship, and giving/offering
            filtered_content = speaker_classification_service.filter_content_by_category(
                utterances, 
                classification_result,
                exclude_categories=[
                    SpeakerCategory.automated_announcements, 
                    SpeakerCategory.worship, 
                    SpeakerCategory.giving_offering
                ]
            )
            
            # Create processed transcript structure
            processed_transcript_data = {
                "processed_at": datetime.now(UTC).isoformat(),
                "version": "2.0",
                "classification_method": "ai_powered",
                "speaker_classifications": [
                    {
                        "speaker_id": speaker.speaker_id,
                        "category": speaker.category,
                        "confidence": speaker.confidence,
                        "word_count": speaker.word_count,
                        "sample_text": speaker.sample_text
                    } for speaker in classification_result.speakers
                ],
                "classification_metadata": {
                    "total_speakers": len(classification_result.speakers),
                    "processing_time_ms": classification_result.processing_time_ms,
                    "api_cost_cents": classification_result.api_cost_cents,
                    "model_used": classification_result.metadata.get("model_used")
                },
                "filtered_content": {
                    "full_text": filtered_content["filtered_text"],
                    "word_count": filtered_content["word_count"],
                    "utterance_count": filtered_content["utterance_count"],
                    "total_duration": filtered_content["total_duration"],
                    "category_breakdown": filtered_content["category_breakdown"],
                    "filters_applied": filtered_content["filters_applied"]
                }
            }
            
            # Update transcript with processed results
            await supabase_service.update_transcript_system(
                transcript_id,
                {
                    "processed_transcript": processed_transcript_data,
                    "processing_status": "completed"
                },
                transcript.created_by
            )
            
            logger.info(f"✅ AI classification completed for transcript {transcript_id}")
            logger.info(f"📊 Speakers: {[s.category for s in classification_result.speakers]}")
            logger.info(f"📊 Filtered: {filtered_content['word_count']} words, {filtered_content['utterance_count']} utterances")
            
        except Exception as e:
            # Update processing status to failed
            await supabase_service.update_transcript_system(
                transcript_id,
                {"processing_status": "failed"},
                transcript.created_by
            )
            raise  # Re-raise for job retry logic

# Global singleton instance
background_job_service = BackgroundJobService()
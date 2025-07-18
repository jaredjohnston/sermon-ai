-- Migration: Add processing_status field for webhook architecture refactor
-- Phase 1: Database schema updates
-- 
-- This migration adds independent status tracking for:
-- 1. Deepgram transcription status (existing 'status' field)
-- 2. AI processing status (new 'processing_status' field)
--
-- This separates concerns and enables the fast acknowledge webhook pattern

-- Step 1: Create new ENUM for processing status
CREATE TYPE processing_status AS ENUM ('pending', 'processing', 'completed', 'failed');

-- Step 2: Add processing_status column to transcripts table
ALTER TABLE public.transcripts 
ADD COLUMN processing_status processing_status NOT NULL DEFAULT 'pending';

-- Step 3: Create index for efficient querying by processing status
CREATE INDEX idx_transcripts_processing_status 
ON public.transcripts(processing_status) 
WHERE deleted_at IS NULL;

-- Step 4: Update existing transcript_status ENUM to be more specific
-- Note: We're keeping the existing values but clarifying they refer to Deepgram transcription
COMMENT ON TYPE transcript_status IS 'Status of Deepgram transcription: processing, completed, failed';
COMMENT ON TYPE processing_status IS 'Status of AI speaker classification processing: pending, processing, completed, failed';

-- Step 5: Add column comments for clarity
COMMENT ON COLUMN public.transcripts.status IS 'Deepgram transcription status - indicates if raw transcript is available';
COMMENT ON COLUMN public.transcripts.processing_status IS 'AI processing status - indicates if speaker classification and content filtering is complete';

-- Step 6: Set initial processing_status values based on existing data
-- If transcript has processed_transcript data, mark as completed
-- Otherwise, mark as pending if transcription is completed, or pending if still processing
UPDATE public.transcripts 
SET processing_status = CASE 
    WHEN processed_transcript IS NOT NULL 
        AND processed_transcript != '{}'::jsonb 
        AND processed_transcript ? 'classification_method' 
    THEN 'completed'::processing_status
    WHEN status = 'completed'::transcript_status 
    THEN 'pending'::processing_status
    ELSE 'pending'::processing_status
END;

-- Step 7: Update any failed transcripts to have failed processing status too
UPDATE public.transcripts 
SET processing_status = 'failed'::processing_status 
WHERE status = 'failed'::transcript_status;

-- Verification queries (for reference - do not run automatically):
--
-- Check the distribution of statuses:
-- SELECT status, processing_status, COUNT(*) 
-- FROM public.transcripts 
-- WHERE deleted_at IS NULL 
-- GROUP BY status, processing_status;
--
-- Check for transcripts ready for AI processing:
-- SELECT COUNT(*) 
-- FROM public.transcripts 
-- WHERE status = 'completed' 
--   AND processing_status = 'pending' 
--   AND deleted_at IS NULL;
-- Migration: Add metadata field to transcripts table
-- Date: 2024-12-27
-- Purpose: Store audio cleanup schedule and other transcript metadata

-- Add metadata column to transcripts table
ALTER TABLE public.transcripts 
ADD COLUMN metadata JSONB DEFAULT '{}'::jsonb;

-- Add index for efficient metadata queries (for audio cleanup)
CREATE INDEX idx_transcripts_metadata_audio_cleanup 
ON public.transcripts USING GIN ((metadata->'audio_cleanup_scheduled')) 
WHERE deleted_at IS NULL;

-- Add index for audio storage path queries
CREATE INDEX idx_transcripts_metadata_audio_path 
ON public.transcripts USING GIN ((metadata->'audio_storage_path')) 
WHERE deleted_at IS NULL;

-- Add comment to document the field
COMMENT ON COLUMN public.transcripts.metadata IS 'JSON metadata including audio cleanup schedule, storage paths, and other transcript-specific data';
-- Migration: Rename videos table to media and expand content type support
-- Purpose: Support multi-content types (video, audio, documents) with consistent naming
-- Date: 2025-06-27
-- GitHub Issue: https://github.com/jaredjohnston/sermon-ai-backend/issues/4

-- Step 1: Rename the table
ALTER TABLE public.videos RENAME TO media;

-- Step 2: Update the content_type constraint to support expanded MIME types
-- Remove the old constraint
ALTER TABLE public.media DROP CONSTRAINT IF EXISTS videos_content_type_check;

-- Add new expanded constraint supporting video, audio, and sermon document types
ALTER TABLE public.media ADD CONSTRAINT media_content_type_check 
CHECK (content_type IN (
    -- Video types
    'video/mp4', 'video/mpeg', 'video/webm',
    -- Audio types  
    'audio/mpeg', 'audio/wav', 'audio/mp3', 'audio/x-m4a', 'audio/mpeg3', 'audio/x-mpeg-3', 'audio/m4a',
    -- Sermon document types
    'text/plain', 'text/markdown', 'text/html',
    'application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/rtf'
));

-- Step 3: Update foreign key constraints in transcripts table
-- The foreign key should now reference media table
ALTER TABLE public.transcripts DROP CONSTRAINT IF EXISTS transcripts_video_id_fkey;
ALTER TABLE public.transcripts ADD CONSTRAINT transcripts_media_id_fkey 
    FOREIGN KEY (video_id) REFERENCES public.media(id) ON DELETE CASCADE;

-- Step 4: Update any indexes that reference the old table name
-- Note: PostgreSQL automatically updates index names when renaming tables, but we'll be explicit
DROP INDEX IF EXISTS idx_videos_client_id;
DROP INDEX IF EXISTS idx_videos_created_by;
DROP INDEX IF EXISTS idx_videos_storage_path;

CREATE INDEX IF NOT EXISTS idx_media_client_id ON public.media(client_id);
CREATE INDEX IF NOT EXISTS idx_media_created_by ON public.media(created_by);
CREATE INDEX IF NOT EXISTS idx_media_storage_path ON public.media(storage_path);

-- Step 5: Update any views or functions that reference videos table
-- (Add any custom views/functions here if they exist)

-- Step 6: RLS (Row Level Security) policies
-- Note: RLS is currently disabled - will be addressed in future security implementation
-- Skipping RLS policy updates for now

-- Step 7: Add comments for documentation
COMMENT ON TABLE public.media IS 'Stores uploaded media files (video, audio, documents) for transcription and processing';
COMMENT ON COLUMN public.media.content_type IS 'MIME type of the uploaded media file - supports video, audio, text, and document formats';
COMMENT ON COLUMN public.media.filename IS 'Original filename of the uploaded media';
COMMENT ON COLUMN public.media.storage_path IS 'Path to the media file in Supabase storage';

-- Step 8: Verification queries (commented out - uncomment to verify after migration)
/*
-- Verify table rename
SELECT COUNT(*) as media_count FROM public.media;

-- Verify constraint
SELECT conname, consrc FROM pg_constraint WHERE conrelid = 'public.media'::regclass AND conname = 'media_content_type_check';

-- Verify foreign keys
SELECT conname, confrelid::regclass as referenced_table FROM pg_constraint 
WHERE conrelid = 'public.transcripts'::regclass AND conname = 'transcripts_media_id_fkey';

-- Verify indexes
SELECT indexname FROM pg_indexes WHERE tablename = 'media' AND schemaname = 'public';

-- Verify RLS policies (skipped - RLS currently disabled)
*/

-- Migration completed successfully
-- Next steps: Update backend code to use 'media' instead of 'videos'
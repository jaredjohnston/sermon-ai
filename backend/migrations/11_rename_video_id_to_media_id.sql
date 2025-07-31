-- Migration: Rename transcripts.video_id to transcripts.media_id
-- Date: 2025-07-31
-- Purpose: Clean up naming to reflect that this field references media records (not just videos)

-- =======================
-- FORWARD MIGRATION
-- =======================

BEGIN;

-- Step 1: Check if the column exists and has the expected name
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'transcripts' 
        AND column_name = 'video_id'
        AND table_schema = 'public'
    ) THEN
        RAISE EXCEPTION 'Column transcripts.video_id does not exist. Migration may have already been applied.';
    END IF;
    
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'transcripts' 
        AND column_name = 'media_id'
        AND table_schema = 'public'
    ) THEN
        RAISE EXCEPTION 'Column transcripts.media_id already exists. Migration conflict detected.';
    END IF;
END $$;

-- Step 2: Rename the column
ALTER TABLE public.transcripts 
RENAME COLUMN video_id TO media_id;

-- Step 3: Update any foreign key constraints
-- Note: Supabase/PostgreSQL typically handles FK updates automatically when renaming columns
-- But let's verify the constraint still exists and points correctly

-- Step 4: Update any indexes that reference the old column name
-- (Most indexes should automatically update with column rename)

-- Step 5: Add a comment to document the change
COMMENT ON COLUMN public.transcripts.media_id IS 'Foreign key reference to media.id - supports all media types (audio, video, documents)';

COMMIT;

-- =======================
-- ROLLBACK SCRIPT (if needed)
-- =======================

-- To rollback this migration, run:
-- BEGIN;
-- ALTER TABLE public.transcripts RENAME COLUMN media_id TO video_id;
-- COMMENT ON COLUMN public.transcripts.video_id IS 'Foreign key reference to media.id';
-- COMMIT;
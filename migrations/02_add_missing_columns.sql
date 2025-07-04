-- Migration to add missing user_id columns and constraints
-- Run this in Supabase SQL Editor

-- Step 1: Check if we have existing data
DO $$
BEGIN
    RAISE NOTICE 'Checking existing data...';
    RAISE NOTICE 'Videos count: %', (SELECT COUNT(*) FROM public.videos);
    RAISE NOTICE 'Transcripts count: %', (SELECT COUNT(*) FROM public.transcripts);
END $$;

-- Step 2: Add user_id column to videos table (nullable first)
ALTER TABLE public.videos 
ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id);

-- Step 3: Add user_id column to transcripts table (nullable first)
ALTER TABLE public.transcripts 
ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id);

-- Step 4: Update existing records (if any) with user_id from created_by
-- For videos table
UPDATE public.videos 
SET user_id = created_by 
WHERE user_id IS NULL AND created_by IS NOT NULL;

-- For transcripts table  
UPDATE public.transcripts 
SET user_id = created_by 
WHERE user_id IS NULL AND created_by IS NOT NULL;

-- Step 5: Handle any remaining NULL user_id records
-- If there are records without created_by, you'll need to assign them to a valid user
-- Uncomment and modify this if needed:
-- UPDATE public.videos SET user_id = 'YOUR_USER_UUID_HERE' WHERE user_id IS NULL;
-- UPDATE public.transcripts SET user_id = 'YOUR_USER_UUID_HERE' WHERE user_id IS NULL;

-- Step 6: Add NOT NULL constraints (only after all records have user_id populated)
DO $$
BEGIN
    -- Check if any NULL user_id records remain
    IF (SELECT COUNT(*) FROM public.videos WHERE user_id IS NULL) > 0 THEN
        RAISE EXCEPTION 'Cannot add NOT NULL constraint: videos table has % records with NULL user_id', 
            (SELECT COUNT(*) FROM public.videos WHERE user_id IS NULL);
    END IF;
    
    IF (SELECT COUNT(*) FROM public.transcripts WHERE user_id IS NULL) > 0 THEN
        RAISE EXCEPTION 'Cannot add NOT NULL constraint: transcripts table has % records with NULL user_id', 
            (SELECT COUNT(*) FROM public.transcripts WHERE user_id IS NULL);
    END IF;
    
    -- Add NOT NULL constraints
    ALTER TABLE public.videos ALTER COLUMN user_id SET NOT NULL;
    ALTER TABLE public.transcripts ALTER COLUMN user_id SET NOT NULL;
    
    RAISE NOTICE 'Successfully added NOT NULL constraints to user_id columns';
END $$;

-- Step 7: Add missing unique constraint on storage_path
DO $$
BEGIN
    -- Check if constraint already exists
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE table_name = 'videos' 
        AND constraint_name = 'videos_storage_path_unique'
        AND table_schema = 'public'
    ) THEN
        ALTER TABLE public.videos 
        ADD CONSTRAINT videos_storage_path_unique UNIQUE (storage_path);
        RAISE NOTICE 'Added unique constraint on videos.storage_path';
    ELSE
        RAISE NOTICE 'Unique constraint on videos.storage_path already exists';
    END IF;
END $$;

-- Step 8: Add missing indexes for performance
CREATE INDEX IF NOT EXISTS idx_videos_user_id ON public.videos(user_id);
CREATE INDEX IF NOT EXISTS idx_transcripts_user_id ON public.transcripts(user_id);

-- Step 9: Verify the changes
DO $$
BEGIN
    RAISE NOTICE 'Migration completed successfully!';
    RAISE NOTICE 'Videos table now has user_id column: %', 
        (SELECT column_name FROM information_schema.columns 
         WHERE table_name = 'videos' AND column_name = 'user_id' LIMIT 1) IS NOT NULL;
    RAISE NOTICE 'Transcripts table now has user_id column: %', 
        (SELECT column_name FROM information_schema.columns 
         WHERE table_name = 'transcripts' AND column_name = 'user_id' LIMIT 1) IS NOT NULL;
    RAISE NOTICE 'Videos storage_path unique constraint exists: %',
        (SELECT constraint_name FROM information_schema.table_constraints 
         WHERE table_name = 'videos' AND constraint_name = 'videos_storage_path_unique' LIMIT 1) IS NOT NULL;
END $$; 
-- RLS Policies for Supabase Storage Direct Upload
-- These policies follow the SermonAI Database Guide standards
-- and enforce client-based access control for file uploads

-- NOTE: The storage.objects policies are supplementary to the main media table policies
-- The media table already has proper RLS policies as defined in SUPABASE_DATABASE_GUIDE.md

-- Enable RLS on storage.objects (if not already enabled)
ALTER TABLE storage.objects ENABLE ROW LEVEL SECURITY;

-- Policy 1: Allow users to upload files to their client's storage path
-- This aligns with the storage_path pattern used in the media table
CREATE OR REPLACE POLICY "users_can_upload_to_client_path" 
ON storage.objects 
FOR INSERT 
TO authenticated
WITH CHECK (
    bucket_id = 'videos' 
    AND
    -- Use standard client isolation pattern from database guide
    -- Extract client_id from storage path and verify user is member
    CASE 
        WHEN name ~ '^uploads/[0-9a-f-]{36}/' THEN
            -- Parse client_id from path: uploads/{client_id}/videos/filename.mp4
            (SPLIT_PART(name, '/', 2))::uuid IN (
                SELECT client_id
                FROM client_users
                WHERE user_id = auth.uid()
                AND deleted_at IS NULL
            )
        ELSE false
    END
);

-- Policy 2: Allow users to read files from their client's storage path
CREATE OR REPLACE POLICY "users_can_read_client_files"
ON storage.objects
FOR SELECT
TO authenticated
USING (
    bucket_id = 'videos'
    AND
    -- Use same pattern as upload policy
    CASE 
        WHEN name ~ '^uploads/[0-9a-f-]{36}/' THEN
            (SPLIT_PART(name, '/', 2))::uuid IN (
                SELECT client_id
                FROM client_users
                WHERE user_id = auth.uid()
                AND deleted_at IS NULL
            )
        ELSE false
    END
);

-- Policy 3: Allow users to update files in their client's storage path
CREATE OR REPLACE POLICY "users_can_update_client_files"
ON storage.objects
FOR UPDATE
TO authenticated
USING (
    bucket_id = 'videos'
    AND
    CASE 
        WHEN name ~ '^uploads/[0-9a-f-]{36}/' THEN
            (SPLIT_PART(name, '/', 2))::uuid IN (
                SELECT client_id
                FROM client_users
                WHERE user_id = auth.uid()
                AND deleted_at IS NULL
            )
        ELSE false
    END
);

-- Policy 4: Allow users to delete files from their client's storage path
CREATE OR REPLACE POLICY "users_can_delete_client_files"
ON storage.objects
FOR DELETE
TO authenticated
USING (
    bucket_id = 'videos'
    AND
    CASE 
        WHEN name ~ '^uploads/[0-9a-f-]{36}/' THEN
            (SPLIT_PART(name, '/', 2))::uuid IN (
                SELECT client_id
                FROM client_users
                WHERE user_id = auth.uid()
                AND deleted_at IS NULL
            )
        ELSE false
    END
);

-- Policy 5: Service role can manage all storage objects (for system operations)
CREATE OR REPLACE POLICY "service_role_full_access"
ON storage.objects
FOR ALL
TO service_role
USING (bucket_id = 'videos')
WITH CHECK (bucket_id = 'videos');

-- Enable RLS on storage.buckets
ALTER TABLE storage.buckets ENABLE ROW LEVEL SECURITY;

-- Policy 6: Allow authenticated users to access the sermon-ai-storage bucket
CREATE OR REPLACE POLICY "authenticated_bucket_access"
ON storage.buckets
FOR SELECT
TO authenticated
USING (id = 'videos');

-- Policy 7: Service role full bucket access
CREATE OR REPLACE POLICY "service_role_bucket_access"
ON storage.buckets
FOR ALL
TO service_role
USING (id = 'videos')
WITH CHECK (id = 'videos');

-- Debugging function to test client_id extraction
CREATE OR REPLACE FUNCTION test_storage_path_parsing(storage_path text)
RETURNS TABLE(
    path text,
    client_id_extracted uuid,
    is_valid_format boolean
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        storage_path as path,
        CASE 
            WHEN storage_path ~ '^uploads/[0-9a-f-]{36}/' THEN
                (SPLIT_PART(storage_path, '/', 2))::uuid
            ELSE NULL
        END as client_id_extracted,
        storage_path ~ '^uploads/[0-9a-f-]{36}/' as is_valid_format;
END;
$$ LANGUAGE plpgsql;

-- Example usage:
-- SELECT * FROM test_storage_path_parsing('uploads/65786eca-36e3-4ac2-8da3-2cc6a2e1030f/videos/sermon.mp4');

-- Verification query to test user's storage access
-- Run this as an authenticated user to verify they can only see their client's files
-- SELECT 
--     name,
--     bucket_id,
--     SPLIT_PART(name, '/', 2)::uuid as extracted_client_id
-- FROM storage.objects 
-- WHERE bucket_id = 'videos'
-- LIMIT 5;
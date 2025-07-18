-- =================================================================
-- SUPABASE STORAGE UPLOAD TRIGGER SETUP
-- =================================================================
-- This script sets up a database trigger that automatically calls
-- your FastAPI webhook when files are uploaded to the 'sermons' bucket
-- =================================================================

-- Step 1: Create the trigger function
-- This function will be called every time a file is inserted into storage.objects
CREATE OR REPLACE FUNCTION invoke_storage_upload_webhook()
RETURNS TRIGGER AS $$
BEGIN
  -- Only process uploads to the 'sermons' bucket
  IF NEW.bucket_id = 'sermons' THEN
    
    -- Log the upload for debugging
    RAISE LOG 'File uploaded to sermons bucket: %', NEW.name;
    
    -- Call the Edge Function using supabase_functions.http_request
    -- This will forward the event to your FastAPI webhook
    PERFORM
      supabase_functions.http_request(
        'POST',
        -- Edge Function URL (will be auto-resolved to your project)
        format('https://%s/functions/v1/storage-upload-webhook', 
               current_setting('app.settings.api_url', true)),
        -- Headers
        jsonb_build_object(
          'Content-Type', 'application/json'
        ),
        -- Payload - matches what your FastAPI webhook expects
        jsonb_build_object(
          'object_name', NEW.name,
          'bucket_name', 'sermons'
        ),
        -- Timeout in milliseconds (5 seconds)
        5000
      );
      
    -- Log successful trigger
    RAISE LOG 'Webhook trigger sent for file: %', NEW.name;
    
  END IF;
  
  -- Always return NEW for AFTER INSERT triggers
  RETURN NEW;
  
EXCEPTION
  -- If webhook call fails, log the error but don't fail the file upload
  WHEN OTHERS THEN
    RAISE WARNING 'Storage webhook trigger failed for file %: %', NEW.name, SQLERRM;
    RETURN NEW;
    
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Step 2: Create the trigger
-- This attaches our function to the storage.objects table
DROP TRIGGER IF EXISTS on_sermons_upload ON storage.objects;

CREATE TRIGGER on_sermons_upload
  AFTER INSERT ON storage.objects
  FOR EACH ROW
  EXECUTE FUNCTION invoke_storage_upload_webhook();

-- =================================================================
-- VERIFICATION QUERIES
-- =================================================================
-- Run these to verify everything was created successfully

-- Check if the trigger function exists
SELECT 
  proname as function_name,
  prosrc as function_body
FROM pg_proc 
WHERE proname = 'invoke_storage_upload_webhook';

-- Check if the trigger exists
SELECT 
  trigger_name,
  event_manipulation,
  action_timing,
  action_statement
FROM information_schema.triggers 
WHERE trigger_name = 'on_sermons_upload';

-- Check triggers on storage.objects table
SELECT 
  trigger_name,
  action_timing,
  event_manipulation
FROM information_schema.triggers 
WHERE event_object_table = 'objects' 
  AND event_object_schema = 'storage';

-- =================================================================
-- TESTING
-- =================================================================
-- After running this SQL, test by:
-- 1. Deploy your Edge Function (storage-upload-webhook)
-- 2. Upload a file via your frontend to the 'sermons' bucket
-- 3. Check Edge Function logs in Supabase Dashboard
-- 4. Check your FastAPI logs for webhook calls
-- 
-- Expected flow:
-- File Upload → storage.objects INSERT → Trigger → Edge Function → FastAPI Webhook
-- =================================================================

-- Optional: Enable more detailed logging for debugging
-- SET log_min_messages = 'LOG';
-- SET log_statement = 'all';
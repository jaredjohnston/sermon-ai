# Phase 2: 30-Day Permanent Deletion System

## Overview

This document contains the complete implementation for Phase 2 of the soft deletion system - automated permanent deletion of records that have been soft-deleted for more than 30 days.

## Architecture

1. **Database Function** - SQL function to permanently delete old records and return storage paths
2. **Edge Function** - Supabase function to trigger cleanup and handle storage file deletion
3. **Backend API** - Optional endpoint for manual testing and monitoring
4. **Scheduling** - External service to trigger daily cleanup

---

## Step 1: Database Function

Run this SQL in **Supabase SQL Editor**:

```sql
-- Function to permanently delete records older than 30 days
CREATE OR REPLACE FUNCTION cleanup_old_deleted_records()
RETURNS TABLE(
    deleted_media_count INTEGER,
    deleted_transcript_count INTEGER,
    deleted_generated_content_count INTEGER,
    storage_paths TEXT[]
) AS $$
DECLARE
    media_paths TEXT[];
    media_count INTEGER;
    transcript_count INTEGER;
    content_count INTEGER;
BEGIN
    -- Get storage paths before deletion for cleanup
    SELECT ARRAY_AGG(storage_path) INTO media_paths
    FROM media 
    WHERE deleted_at IS NOT NULL 
    AND deleted_at < NOW() - INTERVAL '30 days'
    AND storage_path IS NOT NULL;
    
    -- Delete generated content first (child of transcripts)
    DELETE FROM generated_content 
    WHERE transcript_id IN (
        SELECT t.id FROM transcripts t
        JOIN media m ON t.media_id = m.id
        WHERE m.deleted_at IS NOT NULL 
        AND m.deleted_at < NOW() - INTERVAL '30 days'
    );
    GET DIAGNOSTICS content_count = ROW_COUNT;
    
    -- Delete transcripts (child of media)
    DELETE FROM transcripts 
    WHERE media_id IN (
        SELECT id FROM media 
        WHERE deleted_at IS NOT NULL 
        AND deleted_at < NOW() - INTERVAL '30 days'
    );
    GET DIAGNOSTICS transcript_count = ROW_COUNT;
    
    -- Delete media records (parent)
    DELETE FROM media 
    WHERE deleted_at IS NOT NULL 
    AND deleted_at < NOW() - INTERVAL '30 days';
    GET DIAGNOSTICS media_count = ROW_COUNT;
    
    RETURN QUERY SELECT 
        media_count,
        transcript_count, 
        content_count,
        COALESCE(media_paths, ARRAY[]::TEXT[]);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

### Test the Function

```sql
-- Test the function (safe - won't delete anything newer than 30 days)
SELECT * FROM cleanup_old_deleted_records();
```

---

## Step 2: Edge Function

### Create Edge Function Directory

In your terminal:
```bash
cd /Users/jaredjohnston/sermon_ai
mkdir -p supabase/functions/cleanup-deleted-records
```

### Create Edge Function File

Create file: `supabase/functions/cleanup-deleted-records/index.ts`

```typescript
import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    // Verify authorization (optional - remove if using cron)
    const authHeader = req.headers.get('Authorization')
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      console.log('⚠️ No authorization header - proceeding for cron job')
      // For cron jobs, you might want to check a secret instead
      // const secret = req.headers.get('x-cleanup-secret')
      // if (secret !== Deno.env.get('CLEANUP_SECRET')) {
      //   return new Response('Unauthorized', { status: 401 })
      // }
    }

    const supabase = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    )

    console.log('🧹 Starting cleanup of 30+ day old deleted records')

    // Call the database function
    const { data, error } = await supabase.rpc('cleanup_old_deleted_records')
    
    if (error) {
      console.error('❌ Database cleanup failed:', error)
      return new Response(JSON.stringify({ error: error.message }), {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      })
    }

    const result = data[0] || { 
      deleted_media_count: 0, 
      deleted_transcript_count: 0, 
      deleted_generated_content_count: 0, 
      storage_paths: [] 
    }
    
    console.log(`✅ Database cleanup completed:`, result)

    // Clean up storage files if any were deleted
    let cleanedStorageFiles = 0
    if (result.storage_paths && result.storage_paths.length > 0) {
      console.log(`🗂️ Cleaning up ${result.storage_paths.length} storage files`)
      
      for (const path of result.storage_paths) {
        try {
          const { error: storageError } = await supabase.storage
            .from('sermons')
            .remove([path])
          
          if (storageError) {
            console.error(`❌ Failed to delete storage file ${path}:`, storageError)
          } else {
            console.log(`✅ Deleted storage file: ${path}`)
            cleanedStorageFiles++
          }
        } catch (err) {
          console.error(`❌ Error deleting storage file ${path}:`, err)
        }
      }
    }

    const finalResult = {
      success: true,
      deleted_media_count: result.deleted_media_count,
      deleted_transcript_count: result.deleted_transcript_count,
      deleted_generated_content_count: result.deleted_generated_content_count,
      cleaned_storage_files: cleanedStorageFiles,
      total_storage_files_found: result.storage_paths?.length || 0,
      timestamp: new Date().toISOString()
    }

    console.log('🎉 Cleanup completed successfully:', finalResult)

    return new Response(JSON.stringify(finalResult), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })

  } catch (error) {
    console.error('❌ Cleanup function error:', error)
    return new Response(JSON.stringify({ 
      error: error.message,
      timestamp: new Date().toISOString()
    }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })
  }
})
```

### Deploy Edge Function

```bash
# Deploy the edge function
supabase functions deploy cleanup-deleted-records

# Get the function URL (you'll need this for scheduling)
supabase functions list
```

---

## Step 3: Test the System

### Test the Edge Function

```bash
# Test locally (if Supabase CLI is set up)
supabase functions serve

# Test via HTTP
curl -X POST "https://your-project.supabase.co/functions/v1/cleanup-deleted-records" \
  -H "Authorization: Bearer YOUR_ANON_KEY" \
  -H "Content-Type: application/json"
```

### Test with Old Records (for testing)

If you want to test the cleanup immediately, temporarily modify the interval:

```sql
-- TESTING ONLY - Change 30 days to 1 minute for immediate testing
CREATE OR REPLACE FUNCTION cleanup_old_deleted_records_test()
RETURNS TABLE(
    deleted_media_count INTEGER,
    deleted_transcript_count INTEGER,
    deleted_generated_content_count INTEGER,
    storage_paths TEXT[]
) AS $$
-- Change "30 days" to "1 minute" in the function above
-- Then call SELECT * FROM cleanup_old_deleted_records_test();
-- REMEMBER TO RESTORE THE ORIGINAL FUNCTION AFTER TESTING!
```

---

## Step 4: Scheduling Options

### Option A: GitHub Actions (Recommended)

Create `.github/workflows/cleanup-deleted-records.yml`:

```yaml
name: Cleanup Deleted Records

on:
  schedule:
    # Run daily at 2 AM UTC
    - cron: '0 2 * * *'
  workflow_dispatch:  # Allow manual trigger

jobs:
  cleanup:
    runs-on: ubuntu-latest
    steps:
      - name: Call Cleanup Function
        run: |
          curl -X POST "${{ secrets.SUPABASE_FUNCTION_URL }}" \
            -H "Authorization: Bearer ${{ secrets.SUPABASE_ANON_KEY }}" \
            -H "Content-Type: application/json" \
            --fail \
            --show-error \
            --silent
```

Add these secrets to your GitHub repository:
- `SUPABASE_FUNCTION_URL`: `https://your-project.supabase.co/functions/v1/cleanup-deleted-records`
- `SUPABASE_ANON_KEY`: Your Supabase anon key

### Option B: External Cron Service

Use services like:
- **Cron-job.org** (free)
- **EasyCron** 
- **Zapier** (if you have it)

Set up a daily HTTP POST request to your Edge Function URL.

---

## Step 5: Monitoring and Logging

### View Edge Function Logs

```bash
# View logs in real-time
supabase functions logs cleanup-deleted-records --follow
```

### Add Backend Monitoring Endpoint (Optional)

This will be implemented in the FastAPI backend for manual testing and monitoring.

---

## Safety Features

### Built-in Safeguards

1. **30-day minimum** - Only deletes records older than 30 days
2. **Cascade deletion** - Properly handles related records
3. **Storage cleanup** - Removes associated files
4. **Comprehensive logging** - All actions are logged
5. **Error handling** - Graceful failure handling
6. **Transactional** - Database operations are atomic

### Manual Override

If you need to prevent cleanup temporarily:

```sql
-- Disable the function temporarily
DROP FUNCTION IF EXISTS cleanup_old_deleted_records();

-- Re-create when ready to resume
-- (paste the original function definition)
```

---

## Expected Results

When the system runs daily, you should see logs like:

```
🧹 Starting cleanup of 30+ day old deleted records
✅ Database cleanup completed: {deleted_media_count: 3, deleted_transcript_count: 3, deleted_generated_content_count: 8, storage_paths: ['path1', 'path2']}
🗂️ Cleaning up 2 storage files
✅ Deleted storage file: path1
✅ Deleted storage file: path2
🎉 Cleanup completed successfully
```

---

## Next Steps

1. ✅ Run the SQL function in Supabase
2. ✅ Create and deploy the Edge Function  
3. ✅ Test the system manually
4. ✅ Set up automated scheduling
5. ✅ Monitor logs for proper operation

The permanent deletion system will then run automatically, completing the full soft deletion lifecycle!
import { serve } from "https://deno.land/std@0.168.0/http/server.ts"

serve(async (req) => {
  try {
    console.log('Storage upload webhook triggered')
    
    // Get webhook payload from Supabase trigger/Dashboard Webhook
    const payload = await req.json()
    console.log('Received payload:', payload)
    
    // Handle both Dashboard Webhook and legacy formats
    let objectName: string
    let bucketName: string
    let metadata: any = {}
    
    console.log('🔍 Payload detection:', {
      type: payload.type,
      table: payload.table, 
      schema: payload.schema,
      hasRecord: !!payload.record
    })
    
    if (payload.type === 'INSERT' && payload.table === 'objects' && payload.schema === 'storage') {
      // Dashboard Webhook format
      console.log('Processing Dashboard Webhook format')
      const record = payload.record
      
      if (!record) {
        console.error('Missing record in Dashboard Webhook payload')
        return new Response(
          JSON.stringify({ error: 'Missing record in Dashboard Webhook payload' }), 
          { status: 400 }
        )
      }
      
      objectName = record.name
      bucketName = record.bucket_id
      metadata = record.metadata || {}
      
    } else {
      // Legacy format (for manual testing)
      console.log('Processing legacy format')
      objectName = payload.object_name
      bucketName = payload.bucket_name
      metadata = payload.metadata || {}
    }
    
    // Validate required fields
    if (!objectName || !bucketName) {
      console.error('Missing required fields: object_name/name or bucket_name/bucket_id')
      return new Response(
        JSON.stringify({ error: 'Missing object_name/name or bucket_name/bucket_id' }), 
        { status: 400 }
      )
    }
    
    // SMART FILTERING: Only process uploads to the 'sermons' bucket
    if (bucketName !== 'sermons') {
      console.log(`✅ Filter 1 PASSED: Ignoring upload to bucket: ${bucketName}`)
      return new Response(
        JSON.stringify({ message: 'Ignored - not sermons bucket' }), 
        { status: 200 }
      )
    }
    console.log(`✅ Filter 1 PASSED: Bucket is 'sermons'`)
    
    // SMART FILTERING: Check MIME type for audio/video files
    const mimeType = metadata.mimetype || metadata.mimeType || ''
    if (mimeType && !mimeType.startsWith('audio/') && !mimeType.startsWith('video/')) {
      console.log(`✅ Filter 2 PASSED: Ignoring non-audio/video file: ${mimeType}`)
      return new Response(
        JSON.stringify({ message: `Ignored - not audio/video file: ${mimeType}` }), 
        { status: 200 }
      )
    }
    console.log(`✅ Filter 2 PASSED: MIME type is audio/video: ${mimeType}`)
    
    // SMART FILTERING: Check file extension
    const supportedExtensions = ['.mp3', '.mp4', '.wav', '.m4a', '.mpeg', '.webm', '.avi', '.mov']
    const hasValidExtension = supportedExtensions.some(ext => 
      objectName.toLowerCase().endsWith(ext)
    )
    
    if (!hasValidExtension) {
      console.log(`✅ Filter 3 PASSED: Ignoring unsupported file extension: ${objectName}`)
      return new Response(
        JSON.stringify({ message: `Ignored - unsupported file extension: ${objectName}` }), 
        { status: 200 }
      )
    }
    console.log(`✅ Filter 3 PASSED: File extension is supported: ${objectName}`)
    
    console.log(`🎯 ALL FILTERS PASSED - Processing file: ${objectName}`)
    
    // Get environment variables
    const fastApiBaseUrl = Deno.env.get('FASTAPI_BASE_URL')
    const webhookSecret = Deno.env.get('WEBHOOK_SECRET_TOKEN')
    
    if (!fastApiBaseUrl) {
      console.error('FASTAPI_BASE_URL environment variable not set')
      return new Response(
        JSON.stringify({ error: 'FASTAPI_BASE_URL not configured' }), 
        { status: 500 }
      )
    }
    
    if (!webhookSecret) {
      console.error('WEBHOOK_SECRET_TOKEN environment variable not set')
      return new Response(
        JSON.stringify({ error: 'WEBHOOK_SECRET_TOKEN not configured' }), 
        { status: 500 }
      )
    }
    
    // Forward to FastAPI webhook endpoint with normalized payload
    const webhookUrl = `${fastApiBaseUrl}/api/v1/transcription/webhooks/upload-complete`
    console.log(`Forwarding webhook to: ${webhookUrl}`)
    
    // Create normalized payload for FastAPI (legacy format)
    const normalizedPayload = {
      object_name: objectName,
      bucket_name: bucketName,
      metadata: metadata
    }
    
    console.log('Normalized payload for FastAPI:', normalizedPayload)
    
    const response = await fetch(webhookUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${webhookSecret}`
      },
      body: JSON.stringify(normalizedPayload)
    })
    
    const responseText = await response.text()
    console.log(`FastAPI webhook response: ${response.status} - ${responseText}`)
    
    if (response.ok) {
      return new Response(
        JSON.stringify({ 
          success: true, 
          message: 'Webhook forwarded successfully',
          object_name: objectName,
          bucket_name: bucketName,
          filters_passed: 3
        }), 
        { status: 200 }
      )
    } else {
      console.error(`FastAPI webhook failed: ${response.status} - ${responseText}`)
      return new Response(
        JSON.stringify({ 
          error: `FastAPI webhook failed: ${response.status}`,
          details: responseText
        }), 
        { status: 500 }
      )
    }
    
  } catch (error) {
    console.error('Edge function error:', error)
    return new Response(
      JSON.stringify({ 
        error: 'Internal server error',
        details: error.message
      }), 
      { status: 500 }
    )
  }
})
import { apiClient } from "./api-client"
import type { 
  PrepareUploadRequest, 
  TranscriptionResponse, 
  ContentResponse,
  ContentSource,
  ContentTemplatePublic
} from "@/types/api"

// Upload sermon function
export async function uploadSermon(
  file: File,
  onProgress?: (progress: number) => void
): Promise<TranscriptionResponse> {
  try {
    // Prepare upload
    const prepareRequest: PrepareUploadRequest = {
      filename: file.name,
      content_type: file.type,
      size_bytes: file.size,
    }
    
    console.log('Preparing upload for:', prepareRequest)
    const uploadConfig = await apiClient.prepareUpload(prepareRequest)
    console.log('Upload config received:', uploadConfig)
    
    // Upload file using the appropriate method (PUT or TUS)
    console.log(`Uploading using method: ${uploadConfig.upload_method}`)
    await apiClient.uploadFile(
      uploadConfig,
      file,
      onProgress,
      (error) => {
        console.error('Upload failed:', error)
        throw error
      }
    )
    
    console.log('Upload completed successfully')
    
    // After successful upload, we need to trigger the transcription webhook
    // The backend should have already started processing after the upload
    // For now, return a response that matches what the dashboard expects
    // Return media_id initially - the polling system will resolve the transcript_id
    return {
      id: uploadConfig.media_id,
      media_id: uploadConfig.media_id,
      transcript_id: uploadConfig.media_id, // Will be corrected by polling system
      filename: file.name,
      status: "processing", // More accurate status
      created_at: new Date().toISOString(),
      estimated_completion: uploadConfig.processing_info.estimated_processing_time,
    }
  } catch (error) {
    console.error('Upload error details:', error)
    if (error instanceof Error) {
      throw new Error(`Upload failed: ${error.message}`)
    }
    throw new Error('Upload failed: Unknown error')
  }
}

// Generate content function using templates
export async function generateContent(
  transcriptId: string,
  templateId: string,
  customInstructions?: string
): Promise<ContentResponse> {
  try {
    const request = {
      transcript_id: transcriptId,
      template_id: templateId,
      custom_instructions: customInstructions,
    }
    
    const response = await apiClient.generateContent(request)
    
    // Transform the response to match our ContentResponse interface
    return {
      id: response.id,
      content: response.content,
      metadata: {
        generated_at: new Date().toISOString(),
        model_used: "gpt-4o",
        content_type: "template-generated",
        template_id: templateId,
        template_name: "Template", // This would come from the template data
        generation_cost_cents: response.generation_cost_cents,
        generation_duration_ms: response.generation_duration_ms,
      },
    }
  } catch (error) {
    console.error('Content generation error:', error)
    throw error
  }
}

// Create template from examples (pattern extraction + template creation)
export async function createTemplateFromExamples(
  contentTypeName: string,
  examples: string[],
  description?: string
): Promise<ContentTemplatePublic> {
  try {
    const response = await apiClient.extractAndCreateTemplate({
      content_type_name: contentTypeName,
      examples,
      description,
    })
    
    return response
  } catch (error) {
    console.error('Template creation error:', error)
    throw error
  }
}

// List user's templates
export async function getUserTemplates(): Promise<ContentTemplatePublic[]> {
  try {
    return await apiClient.listContentTemplates()
  } catch (error) {
    console.error('Error fetching templates:', error)
    throw error
  }
}

// Export the API client for direct use
export { apiClient }
import { apiClient } from "./api-client"
import type { 
  PrepareUploadRequest, 
  TranscriptionResponse, 
  ContentResponse,
  SermonData,
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
    
    // Upload file
    console.log('Uploading to:', uploadConfig.upload_url)
    const uploadResponse = await apiClient.uploadFile(
      uploadConfig.upload_url,
      uploadConfig.upload_fields,
      file
    )
    
    console.log('Upload response status:', uploadResponse.status)
    if (!uploadResponse.ok) {
      const errorText = await uploadResponse.text()
      console.error('Upload failed with response:', errorText)
      throw new Error(`Upload failed: ${uploadResponse.status} ${uploadResponse.statusText}`)
    }
    
    // After successful upload, we need to trigger the transcription webhook
    // The backend should have already started processing after the upload
    // For now, return a response that matches what the dashboard expects
    return {
      id: uploadConfig.media_id,
      transcript_id: uploadConfig.media_id,
      filename: file.name,
      status: "processing",
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
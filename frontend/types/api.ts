// Re-export all types from shared types
export * from '../../shared/types/api'

// Additional types for frontend components
export interface TranscriptionResponse {
  id: string
  transcript_id: string  // Add this for backend compatibility
  media_id?: string  // Optional media_id for TUS uploads
  filename: string
  status: "processing" | "completed" | "failed"
  created_at: string
  estimated_completion?: string
  transcript?: string
  error_message?: string
}

export interface ContentResponse {
  id: string
  content: string  // Generated content is a single string, not multiple types
  metadata: {
    generated_at: string
    model_used: string
    content_type: string
    template_id: string
    template_name: string
    [key: string]: any
  }
}

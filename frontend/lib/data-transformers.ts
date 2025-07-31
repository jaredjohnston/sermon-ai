/**
 * Data transformation utilities for mapping backend API responses 
 * to frontend TypeScript interfaces
 */

import type { 
  TranscriptResponse, 
  FullTranscriptResponse, 
  GeneratedContentModel,
  ContentSource,
  ProcessingStage,
  ContentGenerationResponse 
} from '@/types/api'

/**
 * Transform backend TranscriptResponse to frontend ContentSource
 */
export function transformTranscriptToContentSource(
  transcript: TranscriptResponse | FullTranscriptResponse,
  generatedContent?: GeneratedContentModel[]
): ContentSource {
  // Determine processing stage based on transcript status
  const getProcessingStage = (status: string, hasContent: boolean): ProcessingStage => {
    switch (status) {
      case 'pending':
      case 'processing':
        return 'transcribing'
      case 'completed':
        return hasContent ? 'completed' : 'transcribing'
      case 'failed':
        return 'error'
      default:
        return 'idle'
    }
  }

  // Extract filename from video data if available
  const getFilename = (transcript: TranscriptResponse | FullTranscriptResponse): string => {
    if ('video' in transcript && transcript.video) {
      return transcript.video.filename
    }
    // Fallback to transcript ID if no filename available
    return `Transcript ${transcript.transcript_id.slice(0, 8)}`
  }

  // Determine source type based on content type
  const getSourceType = (transcript: TranscriptResponse | FullTranscriptResponse): 'audio' | 'video' | undefined => {
    if ('video' in transcript && transcript.video?.content_type) {
      const contentType = transcript.video.content_type
      if (contentType.startsWith('audio/')) return 'audio'
      if (contentType.startsWith('video/')) return 'video'
    }
    return undefined
  }

  const hasContent = 'has_content' in transcript ? transcript.has_content : !!('content' in transcript && transcript.content)
  
  // Use media_id (stored as video_id) as the primary identifier
  // This ensures consistency between upload and list operations
  const mediaId = 'video_id' in transcript 
    ? transcript.video_id 
    : ('video' in transcript && transcript.video ? transcript.video.id : transcript.transcript_id)
  
  return {
    id: mediaId,
    filename: getFilename(transcript),
    transcript: 'content' in transcript ? transcript : undefined,
    content: generatedContent || [],
    uploadedAt: transcript.created_at,
    status: getProcessingStage(transcript.status, hasContent),
    sourceType: getSourceType(transcript)
  }
}

/**
 * Transform array of TranscriptResponse to ContentSource array
 */
export function transformTranscriptListToContentSources(
  transcripts: TranscriptResponse[],
  generatedContentMap?: Map<string, GeneratedContentModel[]>
): ContentSource[] {
  return transcripts.map(transcript => 
    transformTranscriptToContentSource(
      transcript, 
      generatedContentMap?.get(transcript.transcript_id)
    )
  )
}

/**
 * Group generated content by transcript ID for efficient lookup
 */
export function groupGeneratedContentByTranscriptId(
  generatedContent: GeneratedContentModel[]
): Map<string, GeneratedContentModel[]> {
  return generatedContent.reduce((map, content) => {
    const transcriptId = content.transcript_id
    if (!map.has(transcriptId)) {
      map.set(transcriptId, [])
    }
    map.get(transcriptId)!.push(content)
    return map
  }, new Map<string, GeneratedContentModel[]>())
}

/**
 * Check if a ContentSource needs its transcript data fetched
 */
export function needsTranscriptData(contentSource: ContentSource): boolean {
  return (
    contentSource.status === 'completed' && 
    !contentSource.transcript?.content?.full_transcript
  )
}

/**
 * Transform backend ContentGenerationResponse to GeneratedContentModel
 */
export function transformContentGenerationResponse(
  response: ContentGenerationResponse,
  transcriptId: string,
  templateId: string,
  templateName: string
): GeneratedContentModel {
  return {
    id: response.id,
    client_id: '', // This would be set by the backend
    transcript_id: transcriptId,
    template_id: templateId,
    content: response.content,
    content_metadata: {
      ...response.metadata,
      template_name: templateName
    },
    generation_settings: {
      // Backend will populate actual settings
      model: response.metadata?.model_used || 'gpt-4o',
      temperature: response.metadata?.temperature || 0.7
    },
    generation_cost_cents: response.generation_cost_cents,
    generation_duration_ms: response.generation_duration_ms,
    user_edits_count: 0,
    created_at: new Date().toISOString(),
    created_by: '', // This would be set by the backend
    updated_at: new Date().toISOString(),
    updated_by: '' // This would be set by the backend
  }
}
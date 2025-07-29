/**
 * Data transformation utilities for mapping backend API responses 
 * to frontend TypeScript interfaces
 */

import type { 
  TranscriptResponse, 
  FullTranscriptResponse, 
  GeneratedContentModel,
  ContentSource,
  ProcessingStage 
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
  
  return {
    id: transcript.transcript_id,
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
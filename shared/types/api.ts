// TypeScript interfaces for SermonAI Frontend
// Generated from backend schemas

export interface TemplateExtractionRequest {
  content_type_name: string; // User-defined content type (e.g., "small group guide")
  examples: string[]; // 2-5 examples of content
  description?: string; // Optional description
}

export interface PatternExtractionResponse {
  structured_prompt: string;
  confidence_score: number;
  analysis: {
    style_patterns: string[];
    structure_patterns: string[];
    tone_analysis: string;
  };
}

export interface CreateTemplateRequest {
  name: string;
  content_type_name: string;
  structured_prompt: string;
  example_content?: string[];
  description?: string;
  model_settings?: {
    temperature: number;
    max_tokens: number;
    model: string;
  };
}

export interface UpdateTemplateRequest {
  name?: string;
  content_type_name?: string;
  structured_prompt?: string;
  example_content?: string[];
  description?: string;
  status?: "active" | "draft" | "archived";
  model_settings?: {
    temperature: number;
    max_tokens: number;
    model: string;
  };
}

export interface ContentTemplatePublic {
  id: string;
  client_id: string;
  name: string;
  description?: string;
  content_type_name: string;
  // structured_prompt is hidden for IP protection
  example_content: string[];
  status: "active" | "draft" | "archived";
  model_settings: {
    temperature: number;
    max_tokens: number;
    model: string;
  };
  created_at: string;
  created_by: string;
  updated_at: string;
  updated_by: string;
  deleted_at?: string;
  deleted_by?: string;
  creator_name?: string;  // Full name from user profile
}

export interface ContentGenerationRequest {
  transcript_id: string;
  template_id: string;
  custom_instructions?: string;
}

export interface ContentGenerationResponse {
  id: string;
  content: string;
  metadata: Record<string, any>;
  generation_cost_cents?: number;
  generation_duration_ms?: number;
}

export interface GeneratedContentModel {
  id: string;
  client_id: string;
  transcript_id: string;
  template_id: string;
  content: string;
  content_metadata: Record<string, any>;
  generation_settings: Record<string, any>;
  generation_cost_cents?: number;
  generation_duration_ms?: number;
  user_edits_count: number;
  last_edited_at?: string;
  created_at: string;
  created_by: string;
  updated_at: string;
  updated_by: string;
  deleted_at?: string;
  deleted_by?: string;
}

export interface DemoTranscript {
  transcript_id: string;
  title: string;
  transcript: string;
  metadata: {
    speaker: string;
    date: string;
    series: string;
    duration_minutes: number;
  };
}

// Upload and Transcription Types
export interface PrepareUploadRequest {
  filename: string;
  content_type: string;
  size_bytes: number;
}

export interface PrepareUploadResponse {
  upload_url: string;
  upload_fields: Record<string, string>;
  media_id: string;
  processing_info: {
    file_category: "audio" | "video";
    processing_type: string;
    audio_extraction_needed: boolean;
    video_upload_needed: boolean;
    estimated_processing_time: string;
    upload_method: string;
  };
  expires_in: number;
}

export interface TranscriptResponse {
  transcript_id: string;
  video_id: string;
  status: "pending" | "processing" | "completed" | "failed";
  created_at: string;
  updated_at: string;
  estimated_completion?: string;
  error_message?: string;
  request_id?: string;
  has_content: boolean;
}

export interface FullTranscriptResponse {
  transcript_id: string;
  video: {
    id: string;
    filename: string;
    duration_seconds?: number;
    size_bytes: number;
    content_type: string;
  };
  status: "pending" | "processing" | "completed" | "failed";
  content?: {
    full_transcript: string;
    utterances: Array<{
      speaker: number;
      text: string;
      start: number;
      end: number;
      confidence: number;
    }>;
    confidence: number;
  };
  created_at: string;
  updated_at: string;
  completed_at?: string;
  request_id?: string;
  error_message?: string;
}

export interface MediaItem {
  id: string;
  filename: string;
  content_type: string;
  size_bytes: number;
  storage_path: string;
  client_id: string;
  metadata: Record<string, any>;
  created_at: string;
  created_by: string;
  updated_at: string;
  updated_by: string;
}

// Authentication Types
export interface User {
  id: string;
  email: string;
  created_at: string;
  updated_at: string;
}

export interface Client {
  id: string;
  name: string;
  domain?: string;
  settings: Record<string, any>;
  created_at: string;
  created_by: string;
  updated_at: string;
  updated_by: string;
}

// API Configuration
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export const ENDPOINTS = {
  // Auth
  auth: {
    me: "/auth/me",
    refresh: "/auth/refresh",
  },
  // Transcription
  transcription: {
    prepareUpload: "/transcription/upload/prepare",
    upload: "/transcription/upload",
    status: (id: string) => `/transcription/status/${id}`,
    list: "/transcription",
    get: (id: string) => `/transcription/${id}`,
    listVideos: "/transcription/videos",
    getByVideo: (videoId: string) => `/transcription/video/${videoId}`,
    webhookUploadComplete: "/transcription/webhooks/upload-complete",
  },
  // Content Templates & Generation
  content: {
    templates: {
      list: "/content/templates",
      create: "/content/templates",
      get: (id: string) => `/content/templates/${id}`,
      update: (id: string) => `/content/templates/${id}`,
      delete: (id: string) => `/content/templates/${id}`,
    },
    generation: {
      generate: "/content/generate-with-template",
      list: (transcriptId: string) => `/content/generated/transcript/${transcriptId}`,
      get: (id: string) => `/content/generated/${id}`,
    },
    onboarding: {
      extractAndCreateTemplate: "/content/onboarding/extract-and-create-template",
      generateDemoContent: (templateId: string) => `/content/onboarding/generate-demo-content/${templateId}`,
    },
    patterns: {
      extract: "/content/templates/extract",
    },
  },
  // Clients
  clients: {
    list: "/clients",
    get: (id: string) => `/clients/${id}`,
  },
  // Health
  health: "/health",
} as const;

// API Response wrapper types
export interface ApiResponse<T> {
  data: T;
  message?: string;
  error?: string;
}

export interface ApiError {
  detail: string;
  status_code: number;
}

// Frontend State Types
export type ProcessingStage = "idle" | "uploading" | "transcribing" | "generating" | "completed" | "error";

export interface ContentSource {
  id: string;
  filename: string;
  transcript?: FullTranscriptResponse;
  content?: GeneratedContentModel[];
  uploadedAt: string;
  status: ProcessingStage;
  sourceType?: 'audio' | 'video' | 'pdf' | 'docx' | 'text'; // Future extension for documents
}
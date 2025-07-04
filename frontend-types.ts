// TypeScript interfaces for SermonAI Frontend
// Generated from backend schemas

export interface TemplateExtractionRequest {
  content_type_name: string; // User-defined content type (e.g., "small group guide")
  examples: string[]; // 2-5 examples of content
  description?: string; // Optional description
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
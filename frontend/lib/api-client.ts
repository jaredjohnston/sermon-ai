import { 
  API_BASE_URL, 
  ENDPOINTS, 
  PrepareUploadRequest, 
  PrepareUploadResponse,
  TranscriptResponse,
  FullTranscriptResponse,
  ContentTemplatePublic,
  ContentGenerationRequest,
  ContentGenerationResponse,
  GeneratedContentModel,
  MediaItem,
  User,
  ApiError
} from '@/types/api';
import { createClient } from '@/lib/supabase/client';

class ApiClient {
  private baseURL: string;
  private supabase = createClient();

  constructor() {
    this.baseURL = API_BASE_URL;
  }

  // Get fresh token from Supabase session
  private async getToken(): Promise<string | null> {
    const { data: { session } } = await this.supabase.auth.getSession();
    return session?.access_token || null;
  }

  // HTTP client with automatic auth headers
  private async request<T>(
    endpoint: string, 
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    } as Record<string, string>;

    // Add auth header with fresh token from Supabase
    const token = await this.getToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const config: RequestInit = {
      ...options,
      headers,
    };

    try {
      const response = await fetch(url, config);
      
      // Handle non-JSON responses (like file uploads)
      const contentType = response.headers.get('content-type');
      if (!contentType || !contentType.includes('application/json')) {
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return response as unknown as T;
      }

      const data = await response.json();

      if (!response.ok) {
        const error: ApiError = {
          detail: data.detail || data.message || 'Unknown error',
          status_code: response.status
        };
        throw error;
      }

      return data;
    } catch (error) {
      console.error(`API request failed: ${endpoint}`, error);
      throw error;
    }
  }

  // Health check
  async health(): Promise<{ status: string; version: string; timestamp: string }> {
    return this.request(ENDPOINTS.health);
  }

  // Auth endpoints (Supabase Auth handles signup/signin/signout on frontend)
  // Only JWT validation endpoints needed for backend API

  async getCurrentUser(): Promise<User> {
    return this.request(ENDPOINTS.auth.me);
  }

  async refreshToken(): Promise<{ access_token: string }> {
    return this.request(ENDPOINTS.auth.refresh, { method: 'POST' });
  }

  // Transcription endpoints
  async prepareUpload(request: PrepareUploadRequest): Promise<PrepareUploadResponse> {
    return this.request(ENDPOINTS.transcription.prepareUpload, {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async uploadFile(uploadUrl: string, uploadFields: Record<string, string>, file: File): Promise<Response> {
    // Direct upload to Supabase using provided URL and headers
    return fetch(uploadUrl, {
      method: 'PUT',
      headers: uploadFields,
      body: file,
    });
  }

  async getTranscriptionStatus(transcriptId: string): Promise<TranscriptResponse> {
    return this.request(ENDPOINTS.transcription.status(transcriptId));
  }

  async getFullTranscript(transcriptId: string): Promise<FullTranscriptResponse> {
    return this.request(ENDPOINTS.transcription.get(transcriptId));
  }

  async listTranscripts(limit = 20, offset = 0, status?: string): Promise<{
    transcripts: TranscriptResponse[];
    pagination: { total_count: number; limit: number; offset: number; has_more: boolean };
  }> {
    const params = new URLSearchParams({
      limit: limit.toString(),
      offset: offset.toString(),
    });
    if (status) params.append('status_filter', status);
    
    return this.request(`${ENDPOINTS.transcription.list}?${params}`);
  }

  async listVideos(): Promise<MediaItem[]> {
    return this.request(ENDPOINTS.transcription.listVideos);
  }

  // Content template endpoints
  async listContentTemplates(): Promise<ContentTemplatePublic[]> {
    return this.request(ENDPOINTS.content.templates.list);
  }

  async getContentTemplate(templateId: string): Promise<ContentTemplatePublic> {
    return this.request(ENDPOINTS.content.templates.get(templateId));
  }

  async generateContent(request: ContentGenerationRequest): Promise<ContentGenerationResponse> {
    return this.request(ENDPOINTS.content.generation.generate, {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getGeneratedContent(contentId: string): Promise<GeneratedContentModel> {
    return this.request(ENDPOINTS.content.generation.get(contentId));
  }

  async listGeneratedContent(transcriptId: string): Promise<GeneratedContentModel[]> {
    return this.request(ENDPOINTS.content.generation.list(transcriptId));
  }

  // Template extraction for onboarding
  async extractAndCreateTemplate(data: {
    content_type_name: string;
    examples: string[];
    description?: string;
  }): Promise<ContentTemplatePublic> {
    return this.request(ENDPOINTS.content.onboarding.extractAndCreateTemplate, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Webhook trigger (for testing)
  async triggerUploadWebhook(data: { object_name: string; bucket_name?: string }): Promise<any> {
    return this.request(ENDPOINTS.transcription.webhookUploadComplete, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }
}

// Export singleton instance
export const apiClient = new ApiClient();

// Export class for testing
export { ApiClient };

// Utility function for handling API errors in components
export function isApiError(error: any): error is ApiError {
  return error && typeof error.detail === 'string' && typeof error.status_code === 'number';
}

// Hook for React components
export function useApiClient() {
  return apiClient;
}
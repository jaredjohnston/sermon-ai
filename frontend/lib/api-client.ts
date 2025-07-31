import { 
  API_BASE_URL, 
  ENDPOINTS, 
  PrepareUploadRequest, 
  PrepareUploadResponse,
  TUSConfig,
  TranscriptResponse,
  FullTranscriptResponse,
  ContentTemplatePublic,
  ContentGenerationRequest,
  ContentGenerationResponse,
  GeneratedContentModel,
  MediaItem,
  User,
  ApiError,
  CreateTemplateRequest,
  UpdateTemplateRequest,
  PatternExtractionResponse,
  TemplateExtractionRequest
} from '@/types/api';
import { createClient } from '@/lib/supabase/client';
import * as tus from 'tus-js-client';

class ApiClient {
  private baseURL: string;
  private supabase = createClient();

  constructor() {
    this.baseURL = API_BASE_URL;
  }

  // Get fresh token from Supabase session, refresh if needed
  private async getToken(): Promise<string | null> {
    const { data: { session } } = await this.supabase.auth.getSession();
    
    if (!session) {
      return null;
    }
    
    // Check if token is expiring soon (within 5 minutes)
    const expiresAt = session.expires_at;
    const now = Math.floor(Date.now() / 1000);
    const fiveMinutes = 5 * 60;
    
    if (expiresAt && (expiresAt - now) < fiveMinutes) {
      console.log('Token expiring soon, refreshing...');
      const { data: refreshed, error } = await this.supabase.auth.refreshSession();
      
      if (error) {
        console.error('Token refresh failed:', error);
        return session.access_token;
      }
      
      if (refreshed.session) {
        console.log('Token refreshed successfully');
        return refreshed.session.access_token;
      }
    }
    
    return session.access_token;
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
      console.log(`Making request to: ${url}`, { method: config.method, body: config.body });
      const response = await fetch(url, config);
      
      console.log(`Response status: ${response.status} ${response.statusText}`);
      console.log(`Response headers:`, Object.fromEntries(response.headers.entries()));
      
      // Handle non-JSON responses (like file uploads)
      const contentType = response.headers.get('content-type');
      if (!contentType || !contentType.includes('application/json')) {
        console.log('Non-JSON response detected');
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return response as unknown as T;
      }

      const responseText = await response.text();
      console.log(`Raw response text:`, responseText);
      
      let data;
      try {
        data = JSON.parse(responseText);
        console.log(`Parsed response data:`, data);
      } catch (parseError) {
        console.error('Failed to parse JSON response:', parseError);
        throw new Error(`Invalid JSON response: ${responseText}`);
      }

      if (!response.ok) {
        console.error(`API Error ${response.status}:`, data);
        
        // Handle FastAPI validation errors (422)
        let errorMessage = 'Unknown error';
        if (response.status === 422 && data.detail) {
          if (Array.isArray(data.detail)) {
            // Pydantic validation errors are arrays
            errorMessage = data.detail.map((err: any) => `${err.loc?.join('.')}: ${err.msg}`).join(', ');
          } else {
            errorMessage = data.detail;
          }
        } else if (data.detail) {
          errorMessage = data.detail;
        } else if (data.message) {
          errorMessage = data.message;
        }
        
        const error: ApiError = {
          detail: errorMessage,
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

  async uploadFile(
    uploadConfig: PrepareUploadResponse, 
    file: File,
    onProgress?: (progress: number) => void,
    onError?: (error: Error) => void
  ): Promise<void> {
    if (uploadConfig.upload_method === 'tus_resumable' && uploadConfig.tus_config) {
      // For large TUS uploads, ensure we have a fresh token before starting
      const freshToken = await this.getToken();
      if (!freshToken) {
        throw new Error('Authentication required for upload');
      }
      
      // Update the auth header with fresh token
      const updatedConfig = {
        ...uploadConfig.tus_config,
        headers: {
          ...uploadConfig.tus_config.headers,
          'Authorization': `Bearer ${freshToken}`
        }
      };
      // TUS resumable upload for large files
      console.log('TUS Config:', {
        endpoint: updatedConfig.upload_url,
        headers: updatedConfig.headers,
        metadata: updatedConfig.metadata,
        chunk_size: updatedConfig.chunk_size
      });
      
      return new Promise((resolve, reject) => {
        // Remove tus-resumable header since tus-js-client handles it automatically
        const clientHeaders = { ...updatedConfig.headers } as Record<string, string>;
        delete clientHeaders['tus-resumable'];
        
        console.log('Starting TUS upload with config:', {
          endpoint: updatedConfig.upload_url,
          headers: clientHeaders,
          metadata: updatedConfig.metadata,
          chunkSize: updatedConfig.chunk_size,
          fileSize: file.size
        });

        const upload = new tus.Upload(file, {
          endpoint: updatedConfig.upload_url,
          retryDelays: updatedConfig.retry_delays || [0, 1000, 3000, 5000],
          chunkSize: updatedConfig.chunk_size || 6 * 1024 * 1024, // 6MB chunks
          metadata: updatedConfig.metadata || {},
          headers: clientHeaders,
          onError: (error) => {
            console.error('TUS upload failed:', error);
            console.error('TUS error details:', {
              message: error.message,
              stack: error.stack,
              originalRequest: (error as any).originalRequest ? {
                status: (error as any).originalRequest.status,
                responseText: (error as any).originalRequest.responseText,
                getAllResponseHeaders: (error as any).originalRequest.getAllResponseHeaders?.()
              } : null
            });
            onError?.(error);
            reject(error);
          },
          onProgress: (bytesUploaded, bytesTotal) => {
            const progress = Math.round((bytesUploaded / bytesTotal) * 100);
            console.log(`TUS Progress: ${progress}% (${bytesUploaded}/${bytesTotal} bytes)`);
            onProgress?.(progress);
          },
          onSuccess: () => {
            console.log('TUS upload completed successfully');
            resolve();
          }
        });

        upload.start();
      });
    } else {
      // Standard HTTP PUT upload for small files
      try {
        const response = await fetch(uploadConfig.upload_url, {
          method: 'PUT',
          headers: uploadConfig.upload_fields,
          body: file,
        });

        if (!response.ok) {
          throw new Error(`Upload failed: ${response.status} ${response.statusText}`);
        }

        console.log('HTTP PUT upload completed successfully');
      } catch (error) {
        console.error('HTTP PUT upload failed:', error);
        onError?.(error as Error);
        throw error;
      }
    }
  }

  async getTranscriptionStatus(transcriptId: string): Promise<TranscriptResponse> {
    return this.request(ENDPOINTS.transcription.status(transcriptId));
  }

  async getTranscriptByMediaId(mediaId: string): Promise<{
    media_id: string;
    transcript_id: string | null;
    status: string;
    created_at?: string;
    updated_at?: string;
    error_message?: string;
    message?: string;
  }> {
    return this.request(ENDPOINTS.transcription.getTranscriptByMediaId(mediaId));
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

  async createContentTemplate(data: CreateTemplateRequest): Promise<ContentTemplatePublic> {
    return this.request(ENDPOINTS.content.templates.create, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateContentTemplate(templateId: string, data: UpdateTemplateRequest): Promise<ContentTemplatePublic> {
    return this.request(ENDPOINTS.content.templates.update(templateId), {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteContentTemplate(templateId: string): Promise<void> {
    return this.request(ENDPOINTS.content.templates.delete(templateId), {
      method: 'DELETE',
    });
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

  // Pattern extraction methods
  async extractTemplatePatterns(data: TemplateExtractionRequest): Promise<PatternExtractionResponse> {
    return this.request(ENDPOINTS.content.patterns.extract, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Template extraction for onboarding
  async extractAndCreateTemplate(data: TemplateExtractionRequest): Promise<ContentTemplatePublic> {
    return this.request(ENDPOINTS.content.onboarding.extractAndCreateTemplate, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Template CRUD operations
  async createTemplate(data: CreateTemplateRequest): Promise<ContentTemplatePublic> {
    return this.request(ENDPOINTS.content.templates.create, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateTemplate(id: string, data: UpdateTemplateRequest): Promise<ContentTemplatePublic> {
    return this.request(ENDPOINTS.content.templates.update(id), {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteTemplate(id: string): Promise<void> {
    return this.request(ENDPOINTS.content.templates.delete(id), {
      method: 'DELETE',
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
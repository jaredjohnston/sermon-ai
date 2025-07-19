# Frontend-Backend Integration Plan

## Overview
Transform the current dashboard from mock data to a fully functional app that connects to your backend APIs, enabling realistic end-to-end testing.

## Phase 1: Authentication & Environment Setup (Priority: High)

### 1.1 Authentication System
- **Replace placeholder auth headers** in API client with real JWT token management
- **Create login/signup forms** for dashboard authentication
- **Integrate with existing auth endpoints** (`/api/v1/auth/signup`, `/signin`, `/me`)
- **Add environment variables** for API base URL configuration
- **Connect to `generate_fresh_token.py`** workflow for test user creation

### 1.2 Environment Configuration
- **Add `NEXT_PUBLIC_API_URL`** environment variable
- **Configure for development**: `http://localhost:8000/api/v1`
- **Set up proper error handling** for auth failures

## Phase 2: File Upload Integration (Priority: High)

### 2.1 TUS Upload Implementation
- **Replace mock upload in `upload-zone.tsx`** with real TUS integration
- **Connect to backend `/transcription/upload/prepare`** endpoint
- **Implement TUS resumable uploads** using `tus-js-client`
- **Add real progress tracking** (replace simulated progress)
- **Handle upload completion** and webhook triggers

### 2.2 Upload Flow
1. **Prepare Upload**: Call backend to get TUS upload URL
2. **TUS Upload**: Upload file with resume capability
3. **Webhook Processing**: Backend triggers transcription automatically
4. **Status Polling**: Frontend polls for transcription completion

## Phase 3: Sermon Library Integration (Priority: High)

### 3.1 Real Data Integration
- **Replace `SAMPLE_SERMONS`** with real API calls to `/transcription/` endpoints
- **Implement `listTranscripts()`** to fetch user's sermons
- **Add real-time status updates** for transcription progress
- **Show actual file metadata** (size, duration, upload date)

### 3.2 Library Features
- **Search and filtering** based on real data
- **Status indicators** for upload/transcription/processing states
- **"Review Content" button** that shows actual generated content
- **Delete functionality** connected to backend

## Phase 4: Content Template Management (Priority: Medium)

### 4.1 Voice & Style Page
- **Create new component** for template management
- **List user's content templates** via `/content/templates/` endpoint
- **Show template examples** that users provided during creation
- **Display structured prompt confidence scores**
- **Add template creation workflow**

### 4.2 Template Creation Flow
1. **Template Creation Form**: User inputs content type name and examples
2. **Pattern Extraction**: Call `/content/templates/extract` endpoint
3. **Template Storage**: Save via `/content/templates/` endpoint
4. **Template Testing**: Generate demo content to validate

## Phase 5: Content Generation Workflow (Priority: Medium)

### 5.1 Generated Content Integration
- **Replace static content types** in `generated-content.tsx`
- **Connect to `/content/generate-with-template`** endpoint
- **Show actual generated content** from user's templates
- **Add template selection** for content generation
- **Display generation metadata** (cost, duration, confidence)

### 5.2 Generation Flow
1. **Template Selection**: User chooses from their templates
2. **Content Generation**: Backend processes transcript + template
3. **Result Display**: Show generated content with copy/export options
4. **Regeneration**: Allow users to regenerate with different templates

## Phase 6: Real-time Updates & Polish (Priority: Low)

### 6.1 Real-time Features
- **WebSocket/polling** for transcription status updates
- **Live progress indicators** during processing
- **Notifications** for completion/errors
- **Auto-refresh** sermon library when new content is ready

### 6.2 Testing Integration
- **Test user creation** via dashboard (integrate with `generate_fresh_token.py`)
- **File upload testing** (replace `test_frontend_tus.html`)
- **End-to-end content generation** testing
- **Template management** testing

## Implementation Strategy

### Quick Wins (Week 1)
1. **Fix API client authentication** - replace placeholder headers
2. **Connect upload-zone to real TUS** - get file uploads working
3. **Replace sermon library mock data** - show real transcripts

### Core Functionality (Week 2)
1. **Template management page** - create/list/manage templates
2. **Content generation integration** - connect to backend generation
3. **Authentication flow** - login/signup forms

### Polish & Testing (Week 3)
1. **Real-time updates** - status polling and notifications
2. **Error handling** - proper error states and recovery
3. **End-to-end testing** - complete workflow validation

## Key Files to Modify

### High Priority Changes
- `frontend/components/upload-zone.tsx` - Real TUS integration
- `frontend/components/dashboard.tsx` - Replace mock data with API calls
- `frontend/components/sermon-library.tsx` - Real transcript data
- `frontend/dashboard/lib/api-client.ts` - Fix authentication headers

### New Components Needed
- `frontend/components/auth-forms.tsx` - Login/signup forms
- `frontend/components/template-management.tsx` - Voice & style page
- `frontend/components/content-generation.tsx` - Enhanced generation workflow

### Configuration
- `frontend/.env.local` - Environment variables
- `frontend/next.config.mjs` - API proxy configuration

## Testing Strategy

### Development Testing
1. **Start backend**: `python run.py`
2. **Create test user**: `python tests/manual/generate_fresh_token.py`
3. **Start frontend**: `npm run dev`
4. **Test workflow**: Login → Upload → Generate → Review

### Integration Testing
- **File upload flow**: Small and large files
- **Transcription pipeline**: Audio and video processing
- **Template creation**: Various content types
- **Content generation**: Multiple templates per transcript

## Current Status Analysis

### What's Already Ready
- ✅ **Comprehensive API client** with all backend endpoints
- ✅ **Authentication handling** with localStorage token management
- ✅ **Type safety** with shared TypeScript interfaces
- ✅ **Error handling** with proper error types
- ✅ **All endpoints mapped** from backend

### What Needs Integration
- 🔄 Dashboard components still use **mock data** (`SAMPLE_SERMONS`)
- 🔄 Frontend needs to **call real APIs** instead of local data
- 🔄 **Authentication flow** needs to be connected to UI
- 🔄 **Environment variables** need to be configured

## User Experience Goals

### Primary User Flow
1. **Sign in** using test user auth details
2. **Upload file** (replacing `test_frontend_tus.html` functionality)
3. **Wait for transcription** to complete
4. **Create content templates** by providing examples
5. **Generate content** using template + transcript
6. **Review generated content** in dashboard

### Key Pages & Functionality

#### 1. Upload Zone (`upload-zone.tsx`)
- Replace current mock upload with real TUS integration
- Show real progress, not simulated
- Handle large file uploads (>6MB with resumable uploads)

#### 2. Generated Content (`generated-content.tsx`)
- Show actual generated content from templates
- Display real metadata (generation cost, duration)
- Allow template selection for regeneration

#### 3. Voice & Style Page (New Component)
- List user's content templates
- Show examples provided during template creation
- Display structured prompt confidence scores
- Template creation workflow

#### 4. Sermon Library (`sermon-library.tsx`)
- Show real uploaded sermons with actual metadata
- Display real transcription status
- "Review Content" button shows actual generated content
- Delete functionality connected to backend

#### 5. Transcript Editor (`transcript-editor.tsx`)
- **IGNORE** - User editing of transcripts not allowed yet
- Keep component but don't integrate with backend editing

## Technical Implementation Notes

### API Client Status
- **Current**: `frontend/dashboard/lib/api-client.ts` has comprehensive API coverage
- **Issue**: Placeholder auth headers need to be replaced with real JWT tokens
- **Solution**: Integrate with localStorage token management

### Mock Data Removal
- **Current**: `SAMPLE_SERMONS` in `dashboard.tsx` provides fake data
- **Target**: Replace with real API calls to `/transcription/` endpoints
- **Benefit**: Enables realistic testing of entire pipeline

### Environment Configuration
- **Development**: `NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1`
- **Future Production**: `NEXT_PUBLIC_API_URL=https://api.sermonai.com/api/v1`

This plan transforms your dashboard into a fully functional testing environment that mirrors the production workflow: authentication → file upload → transcription → template creation → content generation → review.
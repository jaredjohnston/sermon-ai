# CLAUDE.md - Project Knowledge Base

## 📋 Project Overview

**SermonAI** is an AI-powered platform that automatically transcribes audio/video sermons and generates structured content for churches and religious organizations.

### Purpose
- **Upload**: Large sermon files (audio/video) with reliable resumable uploads
- **Transcribe**: Automatic speech-to-text using Deepgram AI
- **Generate**: Structured content (summaries, key points, etc.) using OpenAI
- **Organize**: Multi-tenant system with client relationship management

### Target Users
- Churches, religious organizations, pastors / church leaders and ministries

## 🛠️ Tools & External Services

### Core Infrastructure
- **Supabase**: Database (PostgreSQL), File Storage, Authentication (JWT)
- **FastAPI**: Python web framework for API backend
- **TUS Protocol**: Resumable file uploads for large files (>6MB)

### AI Services
- **Deepgram**: Speech-to-text transcription (nova-3 model)
- **OpenAI**: Content generation (GPT-4 for summaries, analysis)

### File Processing
- **FFmpeg**: Video-to-audio extraction for transcription
- **Python libraries**: File validation, type detection, streaming

### Development Tools
- **pytest**: Testing framework
- **uvicorn**: ASGI server for local development
- **Supabase CLI**: Database migrations and Edge Functions

## 🚨 Critical Configuration

### **MUST HAVE** Environment Variables
```bash
# Database & Storage
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-key

# AI Services  
DEEPGRAM_API_KEY=your-deepgram-key
OPENAI_API_KEY=your-openai-key

# Security (🚨 CRITICAL)
WEBHOOK_SECRET_TOKEN=your-webhook-secret
JWT_SECRET_KEY=your-jwt-secret
```

### **⚠️ Important Settings**
- **File Size Limit**: 50GB max (Supabase Pro+ limit)
- **TUS Threshold**: 6MB (files >6MB use resumable upload)
- **Chunk Size**: 6MB (Supabase recommended)
- **Supported Formats**: audio/* and video/* only

## 🚀 Development Quick Start

### Local Setup
```bash
# 1. Setup environment
python3 -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env with your API keys and settings

# 3. Start server
cd backend && python run.py  # Runs on http://localhost:8000
```

### 💡 Essential Development Commands
```bash
# Generate fresh test token
cd backend && cd backend && python tests/manual/generate_fresh_token.py

# Run test suite
cd backend && python -m pytest tests/unit/ -v
cd backend && python tests/integration/test_tus_upload_integration.py

# Frontend testing
open backend/tests/manual/test_frontend_tus.html
```

## 🚨 Common Issues & Quick Fixes

### **Upload Problems**
- **"File too large"** → Check file size vs MAX_FILE_SIZE setting
- **"Invalid file type"** → Only audio/* and video/* supported
- **TUS upload fails** → Check token expiration, regenerate if needed

### **Authentication Issues**
- **401 Unauthorized** → Token expired, generate fresh token
- **403 Forbidden** → User not associated with client
- **Missing client** → User must belong to organization

### **Transcription Not Starting**
- **Check webhook setup** → Supabase Storage → FastAPI webhook
- **Verify API keys** → Deepgram and OpenAI keys in .env
- **Monitor logs** → FastAPI server shows webhook calls

### **💡 Quick Diagnostics**
```bash
# Check API health
curl http://localhost:8000/api/v1/health

# Verify token
cd backend && python tests/manual/generate_fresh_token.py

# Test webhook manually
curl -X POST "http://localhost:8000/api/v1/transcription/webhooks/upload-complete" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-webhook-token" \
  -d '{"object_name": "test.mp3", "bucket_name": "sermons"}'
```

## Development Rules
- NEVER mention a co-authored-by or similar aspects. In particular, never mention the tool used to create the commit message or PR.

## 🧠 Architecture Principles and Rules

### Architectural / Development Philosophy
- **Start Simple** → Don't design for scale you don't need yet
- **Separation of Concerns** → Keep logic layered: API / Service / DB
- **Make Data Flow Clear** → Think about how data gets from A → B
- **Maintainable Code is King** → Write code that's easy to update, not just easy to write
- **Handle Errors Properly** → Check inputs, log errors / exceptions, and return helpful error messages
- **Document Decisions** → Use short docs, ARCHITECTURE.md, or ADRs to track trade-offs
- **Write Key Tests** → Focus on business critical integration flows over tiny unit tests
- **Less Code = Less Debt** → Minimize code footprint 

### Other Best Practices
- **Descriptive names** → Use clear and descriptive variable / function names
- **DRY** → Don't repeat yourself
- **Run tests** → Test your code frequently with realistic inputs and validate outputs
- **Simplicity** → Prioritize simplicity and readability over clever solutions
- **Early Returns** → Use to avoid nested conditions

## 🏗️ High Level Architecture

### System Flow Overview
```
Frontend UI → FastAPI Backend → Supabase Storage → AI Processing → Database

```

### **🔄 Data Flow (Upload → Transcription)**
1. **Upload**: Frontend → Backend validation → Supabase Storage (TUS for >6MB files)
2. **Processing**: Storage webhook → Smart routing (audio direct, video extraction)
3. **Transcription**: Signed URL → Deepgram API → Transcript storage
4. **Content Generation**: Transcript → OpenAI API → Structured content
5. **Results**: Database storage → API endpoints → Frontend display

### **👥 Multi-Tenant Architecture**
```
users (individual people)
  ↓ N:1
client_users (relationship table)
  ↓ 1:N  
clients (organizations/churches)
  ↓ 1:N
media & transcripts (isolated by client_id)
```

### **🔐 Authentication & Security**
- **JWT Authentication**: Supabase Auth issues tokens with user_id + client context
- **Client Isolation**: All data scoped to client_id with RLS enforcement
- **API Security**: All endpoints require Bearer token authentication
- **Webhook Security**: Secret token validation for automated triggers

### TLDR Advice:

- **🚫 WEBHOOK ANTI-PATTERN RULE:**

  ### ❌ DON'T DO: Heavy Processing in Webhook Handlers
  - Never perform expensive operations (API calls, complex computations, large database updates) inside webhook endpoints
  - Webhook handlers should complete in <100ms to avoid timeouts and retries
  - Don't mix external service concerns (e.g., Deepgram success + OpenAI success = single status)

  ### ✅ DO: Acknowledge Fast, Process in Background
  - Webhook pattern: Validate → Store minimal data → Queue background job → Return 200 OK immediately
  - Use separate status fields for different concerns (transcription_status vs processing_status)
  - Move heavy operations to background jobs with independent retry logic
  - Keep webhook responses lightweight and fast

  **Remember**: Webhook failures cause retries and cascade issues. Always acknowledge fast and process async. The core principle: Webhooks should acknowledge receipt quickly, not do the work.
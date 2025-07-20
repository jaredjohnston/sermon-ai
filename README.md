# Sermon AI

A FastAPI application for processing sermon audio/video files and generating transcriptions using Deepgram API with Supabase integration.

## Features

- **Audio/Video Transcription**: Direct upload and processing using Deepgram API
- **Smart File Processing**: Automatic detection of audio vs video files with appropriate handling
- **Supabase Integration**: User authentication, file storage, and database management
- **Webhook Processing**: Real-time processing of uploaded files
- **Robust HTTP Client**: SSL-certified HTTP client for reliable external API connections
- **Content Generation**: AI-powered content generation using OpenAI (extensible)

## Prerequisites

- Python 3.12+
- FFmpeg (for video/audio processing)
- Supabase account and project
- Deepgram API key
- OpenAI API key (optional, for content generation)

## Setup

### 1. Clone and Setup Environment

```bash
git clone https://github.com/yourusername/sermon_ai.git
cd sermon_ai

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt
```

### 2. Environment Configuration

Create a `.env` file with your configuration:

```env
# API Keys
DEEPGRAM_API_KEY=your_deepgram_api_key
OPENAI_API_KEY=your_openai_api_key

# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
STORAGE_BUCKET=sermons

# Callback URL (for development with ngrok)
CALLBACK_URL=https://your-ngrok-url.ngrok-free.app/api/v1/transcription/callback

# Application Settings
ENVIRONMENT=development
ADMIN_EMAIL=your-admin@email.com
```

### 3. Database Setup

Ensure your Supabase database has the required tables:
- `users` - User authentication
- `clients` - Organization/client management  
- `media` - File metadata and storage paths
- `transcripts` - Transcription results and status

## Running the Application

### Start the FastAPI Server

```bash
# Using the provided run script
cd backend && python run.py

# Or directly with uvicorn
cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### For Development with Webhooks

1. **Start ngrok tunnel** (required for Deepgram callbacks):
```bash
ngrok http 8000
```

2. **Update callback URL** in `.env` with your ngrok URL:
```env
CALLBACK_URL=https://your-unique-url.ngrok-free.app/api/v1/transcription/callback
```

3. **Restart the server** to use the new callback URL

## API Documentation

- **Interactive API Docs**: `http://localhost:8000/docs`
- **Alternative Docs**: `http://localhost:8000/redoc`
- **Health Check**: `http://localhost:8000/health`

## Key API Endpoints

### Authentication
- `POST /api/v1/auth/signup` - Create new user account
- `POST /api/v1/auth/login` - User login

### Transcription
- `POST /api/v1/transcription/upload/prepare` - Prepare file upload
- `POST /api/v1/transcription/webhooks/upload-complete` - Process uploaded files
- `GET /api/v1/transcription/status/{transcript_id}` - Check transcription status  
- `GET /api/v1/transcription/{transcript_id}` - Get transcript content

### Media Management
- `GET /api/v1/transcription/videos` - List user's media files

## Project Structure

```
sermon_ai/
├── backend/                        # Python FastAPI backend
│   ├── app/
│   │   ├── api/
│   │   │   └── endpoints/
│   │   │       ├── auth.py
│   │   │       ├── transcription.py
│   │   │       ├── content.py
│   │   │       └── health.py
│   │   ├── config/
│   │   │   └── settings.py
│   │   ├── models/
│   │   │   └── schemas.py
│   │   ├── services/
│   │   │   ├── supabase_service.py
│   │   │   ├── deepgram_service.py
│   │   │   ├── audio_extraction_service.py
│   │   │   ├── audio_service.py
│   │   │   ├── validation_service.py
│   │   │   └── file_type_service.py
│   │   ├── utils/
│   │   │   └── http_client.py      # Centralized HTTP client with SSL
│   │   ├── middleware/
│   │   │   └── auth.py
│   │   └── main.py
│   ├── tests/                      # Backend tests
│   ├── migrations/                 # Database migrations
│   ├── requirements.txt
│   ├── run.py
│   └── venv/                       # Virtual environment
├── frontend/                       # Next.js frontend
├── shared/                         # Shared resources
├── supabase/                       # Supabase functions
├── docs/                           # Documentation
└── README.md
```

## Testing

### Run the Test Suite

```bash
# Full transcription pipeline test
cd backend && python tests/unit/test_transcription_pipeline.py

# Generate fresh authentication token
cd backend && python tests/manual/generate_fresh_token.py
```

### Test Requirements

1. **FastAPI server running** on localhost:8000
2. **Valid authentication token** (generate with `generate_fresh_token.py`)
3. **Supabase database accessible**
4. **Test audio file** available at specified path
5. **ngrok tunnel active** (for webhook callbacks)

## Architecture Highlights

### SSL Certificate Handling
- **Centralized HTTP Client**: `app/utils/http_client.py` provides robust SSL handling
- **Environment-aware SSL**: Proper certificate validation using `certifi`
- **Connection pooling**: Efficient HTTP connection management

### File Processing Pipeline
1. **Upload Preparation**: Generate signed URLs for direct client uploads
2. **Smart Routing**: Automatic detection of audio vs video files
3. **Audio Extraction**: FFmpeg-based extraction for video files
4. **Webhook Processing**: Background processing of uploaded files
5. **Transcription**: Deepgram API integration with callback handling

### Security Features
- **JWT Authentication**: Supabase-based user authentication
- **Row Level Security**: Database-level access control
- **Audit Trails**: Comprehensive tracking of created_by/updated_by fields
- **SSL Verification**: Proper certificate validation for all HTTP requests

## Troubleshooting

### Common Issues

1. **SSL Certificate Errors**: Fixed with centralized HTTP client utility
2. **Virtual Environment Issues**: Delete and recreate venv if imports fail
3. **Webhook Timeouts**: Ensure ngrok tunnel is active and URL is correct
4. **File Upload Failures**: Check Supabase storage permissions and bucket configuration

### Development Tips

- **Use fresh tokens**: Generate new auth tokens if authentication fails
- **Monitor logs**: Check FastAPI server logs for detailed error information  
- **Test incrementally**: Use individual test functions to isolate issues
- **Verify environment**: Ensure all API keys and URLs are correctly configured

## License

This project is licensed under the MIT License - see the LICENSE file for details.
import os
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import httpx
import openai
from dotenv import load_dotenv
import uvicorn
from urllib.parse import urlencode

# Load environment variables
print("Attempting to load .env file...")
load_result = load_dotenv()
print(f"Load result: {load_result}")  # Will print True if .env was found and loaded


# Validate required environment variables
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

print("\n=== Checking Environment Variables ===")
print(f"Deepgram API Key present: {'Yes' if DEEPGRAM_API_KEY else 'No'}")
print(f"Deepgram API Key length: {len(DEEPGRAM_API_KEY) if DEEPGRAM_API_KEY else 0}")
print(f"First few characters: {DEEPGRAM_API_KEY[:4]}..." if DEEPGRAM_API_KEY else "None")
print("======================================\n")

if not DEEPGRAM_API_KEY:
    raise ValueError("DEEPGRAM_API_KEY environment variable is required")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is required")

# Initialize OpenAI client
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Initialize FastAPI app
app = FastAPI(title="Sermon Content Generator API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Local Next.js dev
        "https://your-vercel-app.vercel.app",  # Replace with your Vercel domain
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define allowed audio file types
ALLOWED_AUDIO_TYPES = [
    "audio/mpeg",
    "audio/wav",
    "audio/mp3",
    "audio/x-m4a",
    "audio/mpeg3",
    "audio/x-mpeg-3",
    "audio/m4a",
]

# Define allowed video file types
ALLOWED_VIDEO_TYPES = [
    "video/mp4",
    "video/mpeg",
    "video/webm"
]

# Define allowed media types
ALLOWED_MEDIA_TYPES = ALLOWED_AUDIO_TYPES + ALLOWED_VIDEO_TYPES

class TranscriptRequest(BaseModel):
    transcript: str
    content_types: List[str] = ["devotional", "summary", "discussion_questions"]

class ContentResponse(BaseModel):
    content: Dict[str, str]

class TranscriptionResponse(BaseModel):
    message: str
    transcript: str
    filename: str
    size: str
    content_type: str

CONTENT_TYPES = {
    "devotional": {
        "prompt": """Based on the following sermon transcript, create a 3-paragraph devotional that includes:
- A relevant Bible verse
- Three paragraphs of spiritual reflection
- A closing prayer

Sermon Transcript:
{transcript}""",
        "temperature": 0.7,
        "max_tokens": 400
    },
    "summary": {
        "prompt": """Based on the following sermon transcript, write a clear, concise 1-paragraph summary of the sermon's key message.

Sermon Transcript:
{transcript}""",
        "temperature": 0.5,
        "max_tokens": 200
    },
    "discussion_questions": {
        "prompt": """Based on the following sermon transcript, generate 5 thought-provoking discussion questions that explore the main themes and applications of the message.

Sermon Transcript:
{transcript}""",
        "temperature": 0.7,
        "max_tokens": 300
    }
}

# File size limits
MAX_FILE_SIZE = 3 * 1024 * 1024 * 1024  # 3GB limit
STREAM_THRESHOLD = 100 * 1024 * 1024     # Stream files larger than 100MB

@app.post("/transcribe")
async def transcribe_media(file: UploadFile = File(...)):
    try:
        # Validate file type
        if file.content_type not in ALLOWED_MEDIA_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"File type {file.content_type} not supported. Supported types: {ALLOWED_MEDIA_TYPES}"
            )
        
        # Read file content
        content = await file.read()
        file_size = len(content)
        
        # Check file size
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File size ({file_size/1024/1024:.2f} MB) exceeds maximum allowed size (3 GB)"
            )
        
        # Prepare headers for Deepgram API
        headers = {
            "Authorization": f"Token {DEEPGRAM_API_KEY}",
            "Content-Type": file.content_type
        }
        
        # Configure Deepgram parameters
        params = {
            "smart_format": "true",
            "punctuate": "true",
            "diarize": "false",
            "model": "nova-2",
            "language": "en-US"
        }
        
        print(f"\n=== Deepgram API Request ===")
        print(f"Content Type: {file.content_type}")
        print(f"File Size: {file_size/1024/1024:.2f} MB")
        print("===========================\n")
        
        # Send request to Deepgram API
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.deepgram.com/v1/listen?" + urlencode(params),
                headers=headers,
                content=content,
                timeout=300  # 5 minutes timeout for larger files
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=502,
                    detail=f"Deepgram API error: {response.text}"
                )
            
            result = response.json()
            transcript = result["results"]["channels"][0]["alternatives"][0]["transcript"]
            
            print(f"\n=== Transcription Result ===")
            print(f"Transcript length: {len(transcript)}")
            print(f"First 100 chars: {transcript[:100]}...")
            print("===========================\n")
            
            return {
                "message": "Transcription successful",
                "transcript": transcript,
                "filename": file.filename,
                "size": f"{file_size/1024/1024:.2f} MB",
                "content_type": file.content_type
            }
        
    except Exception as e:
        print(f"Transcription error: {str(e)}")
        raise HTTPException(
            status_code=502,
            detail=f"Transcription failed: {str(e)}"
        )

@app.post("/generate", response_model=ContentResponse)
async def generate_content(request: TranscriptRequest):
    print(f"\n=== Generate Content Request ===")
    print(f"Transcript length: {len(request.transcript) if request.transcript else 0}")
    print(f"First 100 chars: {request.transcript[:100]}...")
    print(f"Content types requested: {request.content_types}")
    print("=============================\n")
    
    try:
        results = {}
        for content_type in request.content_types:
            config = CONTENT_TYPES[content_type]
            prompt = config["prompt"].format(transcript=request.transcript)
            
            print(f"\n=== Generating {content_type} ===")
            print(f"Prompt length: {len(prompt)}")

            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a skilled religious content creator, experienced in creating various forms of spiritual content from sermon transcriptions."},
                    {"role": "user", "content": prompt}
                ],
                temperature=config["temperature"],
                max_tokens=config["max_tokens"]
            )
            
            results[content_type] = response.choices[0].message.content
            print(f"Generated {content_type} content length: {len(results[content_type])}")
            print("==========================\n")
        
        return ContentResponse(content=results)
    
    except Exception as e:
        print(f"Content generation error: {str(e)}")
        raise HTTPException(
            status_code=502,
            detail=f"Error generating content: {str(e)}"
        )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

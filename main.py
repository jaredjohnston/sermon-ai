import os
import logging
from datetime import datetime
from fastapi import FastAPI, HTTPException, UploadFile, File, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import httpx
import openai
from dotenv import load_dotenv
import uvicorn
from urllib.parse import urlencode

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
logger.info("Loading environment variables...")
load_dotenv()

# Response Models
class HealthResponse(BaseModel):
    status: str
    version: str = "1.0.0"
    timestamp: str

class TranscriptRequest(BaseModel):
    transcript: str
    content_types: List[str] = Field(
        default=["devotional", "summary", "discussion_questions"],
        description="Types of content to generate"
    )

class ContentResponse(BaseModel):
    content: Dict[str, str]
    generated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class TranscriptionResponse(BaseModel):
    message: str
    transcript: str
    filename: str
    size: str
    content_type: str
    processed_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class ErrorResponse(BaseModel):
    detail: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

# Configuration
class Config:
    DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    MAX_FILE_SIZE = 3 * 1024 * 1024 * 1024  # 3GB
    STREAM_THRESHOLD = 100 * 1024 * 1024     # 100MB
    ALLOWED_AUDIO_TYPES = [
        "audio/mpeg", "audio/wav", "audio/mp3", "audio/x-m4a",
        "audio/mpeg3", "audio/x-mpeg-3", "audio/m4a",
    ]
    ALLOWED_VIDEO_TYPES = ["video/mp4", "video/mpeg", "video/webm"]
    ALLOWED_MEDIA_TYPES = ALLOWED_AUDIO_TYPES + ALLOWED_VIDEO_TYPES
    
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
            "prompt": """Based on the following sermon transcript write two or three sentences that capture the heart of the sermon's message. Please write from the third person perspective, e.g. [Pastor's Name] brought a much-needed message on [Sermon's theme]. Use clear, pastoral language to emphasize how the message applies to discipleship and spiritual growth

Sermon Transcript:
{transcript}""",
            "temperature": 0.5,
            "max_tokens": 200
        },
        "discussion_questions": {
            "prompt": """You are a content creator for a church that produces weekly group study guides based on Sunday sermons. Please read the sermon transcript below and create a clear, structured study guide for small group leaders.

            Follow this exact format:

            Sunday [Date] – Group Study Guide
            Message Title: [Title from sermon]
            Speaker: [Speaker's name]
            Series: [Series title, if mentioned]
            Key Text: [Main scripture reference, ideally from the sermon]

            INTRODUCTION:
            Write 3–5 sentences summarizing the heart of the message. Highlight the theme of the sermon in a way that is theologically sound, spiritually encouraging, and accessible for group discussion. Use engaging, pastoral language that reflects the speaker’s tone.

            1. [First Major Point of the Message (e.g. “Understand the PURPOSE of the Sabbath”)]
            Write a 2–3 sentence summary explaining this point in plain, inspiring language.
            Include 1–3 relevant scripture passages quoted in full (with references).
            Then, write 2 discussion questions that help the group reflect on this teaching.

            2. [Second Major Point (e.g. “Recognise the BARRIERS to Sabbath Rest”)]
            Again, summarize this section of the message in 2–3 sentences.
            Quote relevant scripture verses in full.
            Include 2 discussion questions focused on personal application.

            3. [Third Major Point (e.g. “Receive the BLESSING of the Sabbath”)]
            List out any sub-points (like a., b., c.) clearly.
            For each sub-point:

            Write a brief explanation of the point.

            Include relevant scripture.

            Optional: Include 1–2 extra reflection questions at the end of this section.

            CLOSING PRAYER:
            Write a short (4–6 line) pastoral prayer that reflects the message’s heart and helps group members respond personally to what they’ve heard. Use inclusive “we” language and close in Jesus’ name.

            Important Notes:

            Use headings, bold text, and spacing exactly as in the sample.
            Use uppercase / all-caps for key words in the headings.
            Quote all Bible verses in full and cite the reference.
            The tone should be warm, accessible, and biblically grounded.
            Don’t invent content—only summarise or structure what’s in the transcript.

Sermon Transcript:
{transcript}""",
            "temperature": 0.7,
            "max_tokens": 300
        }
    }

# Validate configuration
if not Config.DEEPGRAM_API_KEY:
    raise ValueError("DEEPGRAM_API_KEY environment variable is required")
if not Config.OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is required")

# Initialize clients
openai_client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)

# Initialize FastAPI app
app = FastAPI(
    title="Sermon Content Generator API",
    description="API for transcribing sermons and generating various content types",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://your-vercel-app.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint to verify API status"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat()
    )

@app.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_media(file: UploadFile = File(...)):
    """Transcribe uploaded audio/video file using Deepgram API"""
    try:
        logger.info(f"Received transcription request for file: {file.filename}")
        
        # Validate file type
        if file.content_type not in Config.ALLOWED_MEDIA_TYPES:
            logger.warning(f"Invalid file type received: {file.content_type}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type {file.content_type} not supported. Supported types: {Config.ALLOWED_MEDIA_TYPES}"
            )
        
        # Read and validate file content
        content = await file.read()
        file_size = len(content)
        
        if file_size > Config.MAX_FILE_SIZE:
            logger.warning(f"File size exceeds limit: {file_size/1024/1024:.2f}MB")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size ({file_size/1024/1024:.2f} MB) exceeds maximum allowed size (3 GB)"
            )
        
        # Prepare Deepgram request
        headers = {
            "Authorization": f"Token {Config.DEEPGRAM_API_KEY}",
            "Content-Type": file.content_type
        }
        
        params = {
            "smart_format": "true",
            "punctuate": "true",
            "diarize": "false",
            "model": "nova-2",
            "language": "en-US"
        }
        
        logger.info(f"Sending request to Deepgram API for file: {file.filename}")
        
        # Process transcription
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.deepgram.com/v1/listen?" + urlencode(params),
                headers=headers,
                content=content,
                timeout=300
            )
            
            if response.status_code != 200:
                logger.error(f"Deepgram API error: {response.text}")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Deepgram API error: {response.text}"
                )
            
            result = response.json()
            transcript = result["results"]["channels"][0]["alternatives"][0]["transcript"]
            
            logger.info(f"Successfully transcribed file: {file.filename}")
            
            return TranscriptionResponse(
                message="Transcription successful",
                transcript=transcript,
                filename=file.filename,
                size=f"{file_size/1024/1024:.2f} MB",
                content_type=file.content_type
            )
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Transcription error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Transcription failed: {str(e)}"
        )

@app.post("/generate", response_model=ContentResponse)
async def generate_content(request: TranscriptRequest):
    """Generate various content types from sermon transcript"""
    try:
        logger.info(f"Received content generation request for {len(request.content_types)} content types")
        
        results = {}
        for content_type in request.content_types:
            if content_type not in Config.CONTENT_TYPES:
                logger.warning(f"Invalid content type requested: {content_type}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid content type: {content_type}"
                )
                
            config = Config.CONTENT_TYPES[content_type]
            prompt = config["prompt"].format(transcript=request.transcript)
            
            logger.info(f"Generating {content_type} content")
            
            response = openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a skilled religious content creator, experienced in creating various forms of spiritual content from sermon transcriptions."},
                    {"role": "user", "content": prompt}
                ],
                temperature=config["temperature"],
                max_tokens=config["max_tokens"]
            )
            
            results[content_type] = response.choices[0].message.content
            logger.info(f"Successfully generated {content_type} content")
        
        return ContentResponse(content=results)
    
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Content generation error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error generating content: {str(e)}"
        )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

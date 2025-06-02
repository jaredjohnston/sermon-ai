import os
import logging
from datetime import datetime
from fastapi import FastAPI, HTTPException, UploadFile, File, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Tuple
import httpx
import openai
from dotenv import load_dotenv
import uvicorn
from urllib.parse import urlencode
from enum import Enum
import json

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
    sermon_text: str = Field(description="The sermon transcript text to generate content from")
    admin_text: Optional[str] = Field(default=None, description="Optional admin announcements text")
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

class SegmentType(str, Enum):
    WORSHIP = "worship"
    WELCOME = "welcome"
    SERMON = "sermon"
    ADMIN = "admin"
    TITHING = "tithing"
    OTHER = "other"

class Segment(BaseModel):
    type: SegmentType
    text: str
    start_time: float
    end_time: float
    confidence: float

class SegmentedTranscriptionResponse(BaseModel):
    message: str
    segments: List[Segment]
    sermon_segments: List[Segment]
    admin_segments: List[Segment]
    filename: str
    size: str
    content_type: str
    processed_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

# Configuration
class Config:
    DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    MAX_FILE_SIZE = 3 * 1024 * 1024 * 1024  # 3GB
    STREAM_THRESHOLD = 100 * 1024 * 1024     # 100MB
    CHUNK_DURATION = 120  # 2 minutes in seconds
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
            Write 3–5 sentences summarizing the heart of the message. Highlight the theme of the sermon in a way that is theologically sound, spiritually encouraging, and accessible for group discussion. Use engaging, pastoral language that reflects the speaker's tone.

            1. [First Major Point of the Message (e.g. "Understand the PURPOSE of the Sabbath")]
            Write a 2–3 sentence summary explaining this point in plain, inspiring language.
            Include 1–3 relevant scripture passages quoted in full (with references).
            Then, write 2 discussion questions that help the group reflect on this teaching.

            2. [Second Major Point (e.g. "Recognise the BARRIERS to Sabbath Rest")]
            Again, summarize this section of the message in 2–3 sentences.
            Quote relevant scripture verses in full.
            Include 2 discussion questions focused on personal application.

            3. [Third Major Point (e.g. "Receive the BLESSING of the Sabbath")]
            List out any sub-points (like a., b., c.) clearly.
            For each sub-point:

            Write a brief explanation of the point.

            Include relevant scripture.

            Optional: Include 1–2 extra reflection questions at the end of this section.

            CLOSING PRAYER:
            Write a short (4–6 line) pastoral prayer that reflects the message's heart and helps group members respond personally to what they've heard. Use inclusive "we" language and close in Jesus' name.

            Important Notes:

            Use headings, bold text, and spacing exactly as in the sample.
            Use uppercase / all-caps for key words in the headings.
            Quote all Bible verses in full and cite the reference.
            The tone should be warm, accessible, and biblically grounded.
            Don't invent content—only summarise or structure what's in the transcript.

Sermon Transcript:
{transcript}""",
            "temperature": 0.7,
            "max_tokens": 300
        }
    }

    SEGMENT_CLASSIFIER_PROMPT = """You are an expert at analyzing church service transcripts. Your task is to classify the following segment of a church service transcript into one of these categories:
- WORSHIP: Musical worship, songs, prayers during worship
- WELCOME: Welcoming new visitors, announcements at the start
- SERMON: The main sermon message, including opening/closing prayers
- ADMIN: Church announcements, upcoming events
- TITHING: Offering, giving, financial matters
- OTHER: Any other segments

Here are some example segments and their classifications:
[Example 1]
"Let's all stand and worship together. ♪ Amazing grace, how sweet the sound ♪"
Classification: WORSHIP
Reason: Contains worship song lyrics and worship-related instruction

[Example 2]
"Today, we're continuing our series on the Book of Romans, chapter 8. Let's pray before we dive into God's Word."
Classification: SERMON
Reason: Introduces the sermon topic and includes a sermon-related prayer

[Example 3]
"Don't forget to join us next Sunday for our church picnic. Sign-up sheets are in the foyer."
Classification: ADMIN
Reason: Contains church announcements and event information

Now, please classify the following segment:
{text}

Respond in the following JSON format only:
{
    "type": "WORSHIP|WELCOME|SERMON|ADMIN|TITHING|OTHER",
    "confidence": 0.0-1.0,
    "reasoning": "Brief explanation of classification"
}"""

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

@app.post("/transcribe", response_model=SegmentedTranscriptionResponse)
async def transcribe_media(file: UploadFile = File(...)):
    """Transcribe uploaded audio/video file using Deepgram API and classify segments"""
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
            "diarize": "true",  # Enable speaker diarization
            "utterances": "true",  # Get utterance-level segments
            "model": "nova-2",
            "language": "en-US"
        }
        
        logger.info("Sending request to Deepgram API")
        
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
            utterances = result["results"]["utterances"]
            
            # Group utterances into 2-minute chunks for efficient processing
            chunks = []
            current_chunk = []
            chunk_start_time = 0
            
            for utterance in utterances:
                if not current_chunk:
                    chunk_start_time = utterance["start"]
                    current_chunk.append(utterance)
                elif utterance["start"] - chunk_start_time <= Config.CHUNK_DURATION:
                    current_chunk.append(utterance)
                else:
                    chunks.append(current_chunk)
                    current_chunk = [utterance]
                    chunk_start_time = utterance["start"]
            
            if current_chunk:
                chunks.append(current_chunk)
            
            # Classify each chunk
            segments = []
            for chunk in chunks:
                chunk_text = " ".join(u["transcript"] for u in chunk)
                chunk_start = chunk[0]["start"]
                chunk_end = chunk[-1]["end"]
                
                # Classify chunk using GPT-4
                classification_response = openai_client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are an expert at analyzing church service transcripts."},
                        {"role": "user", "content": Config.SEGMENT_CLASSIFIER_PROMPT.format(text=chunk_text)}
                    ],
                    temperature=0.3,
                    response_format={"type": "json_object"}
                )
                
                try:
                    classification = classification_response.choices[0].message.content
                    classification_data = json.loads(classification)
                    
                    segment = Segment(
                        type=SegmentType(classification_data["type"].lower()),
                        text=chunk_text,
                        start_time=chunk_start,
                        end_time=chunk_end,
                        confidence=classification_data["confidence"]
                    )
                    segments.append(segment)
                    logger.info(f"Classified segment as {segment.type} with confidence {segment.confidence}")
                except Exception as e:
                    logger.error(f"Error processing classification response: {str(e)}")
                    continue
            
            # Extract sermon and admin segments
            sermon_segments = [s for s in segments if s.type == SegmentType.SERMON]
            admin_segments = [s for s in segments if s.type == SegmentType.ADMIN]
            
            # Merge adjacent sermon segments
            merged_sermon_segments = []
            current_sermon = None
            
            for segment in sermon_segments:
                if not current_sermon:
                    current_sermon = segment
                elif segment.start_time - current_sermon.end_time <= 300:  # 5-minute gap threshold
                    # Merge segments
                    current_sermon.text += f" {segment.text}"
                    current_sermon.end_time = segment.end_time
                    current_sermon.confidence = (current_sermon.confidence + segment.confidence) / 2
                else:
                    merged_sermon_segments.append(current_sermon)
                    current_sermon = segment
            
            if current_sermon:
                merged_sermon_segments.append(current_sermon)
            
            logger.info(f"Successfully processed file: {file.filename}")
            logger.info(f"Found {len(merged_sermon_segments)} sermon segments and {len(admin_segments)} admin segments")
            
            return SegmentedTranscriptionResponse(
                message="Transcription and segmentation successful",
                segments=segments,
                sermon_segments=merged_sermon_segments,
                admin_segments=admin_segments,
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
            prompt = config["prompt"].format(transcript=request.sermon_text)
            
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

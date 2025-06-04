# Sermon AI

A FastAPI application for processing sermon videos and generating various types of content.

## Features

- Video transcription using Deepgram
- Segment classification (sermon, prayer, worship, etc.)
- Content generation:
  - Devotionals
  - Summaries
  - Discussion questions
  - "What's On" announcements

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/sermon_ai.git
cd sermon_ai
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file with your API keys:
```
OPENAI_API_KEY=your_openai_key
DEEPGRAM_API_KEY=your_deepgram_key
```

## Running the Application

Start the FastAPI server:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`
- API documentation: `http://localhost:8000/docs`
- Alternative documentation: `http://localhost:8000/redoc`

## API Endpoints

### POST /api/v1/transcribe
Transcribe a video and classify its segments.

Request body:
```json
{
    "video_url": "https://example.com/video.mp4",
    "mime_type": "video/mp4"
}
```

### POST /api/v1/generate
Generate content from classified segments.

Request body:
```json
{
    "segments": [
        {
            "type": "sermon",
            "text": "segment text",
            "start_time": 0.0,
            "end_time": 60.0,
            "confidence": 0.95
        }
    ],
    "content_type": "devotional"
}
```

## Project Structure

```
sermon_ai/
├── app/
│   ├── api/
│   │   └── endpoints.py
│   ├── config/
│   │   └── settings.py
│   ├── models/
│   │   └── schemas.py
│   ├── services/
│   │   ├── classifier_service.py
│   │   ├── content_service.py
│   │   └── transcription_service.py
│   └── main.py
├── requirements.txt
└── README.md
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 
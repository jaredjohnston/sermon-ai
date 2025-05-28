# Sermon Content Generator API

This is a FastAPI-based backend application that transforms sermon audio into various forms of content using AI, including devotionals, summaries, and discussion questions.

## Setup

1. Clone the repository
2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory with your API keys:
```
OPENAI_API_KEY=your_openai_api_key_here
DEEPGRAM_API_KEY=your_deepgram_api_key_here
```

## Running the Application

Start the FastAPI server:
```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

## API Endpoints

### POST /transcribe
- Transcribes audio files using Deepgram API
- Request: `multipart/form-data`
  - Field name: `file`
  - Supported audio formats: MP3, WAV, etc.
- Returns: Raw Deepgram JSON response with timestamps

Example curl request:
```bash
curl -X POST http://localhost:8000/transcribe \
  -H "Content-Type: multipart/form-data" \
  -F "file=@path/to/your/sermon.mp3"
```

### POST /generate
- Generates content from sermon transcript
- Request body:
```json
{
    "transcript": "Your sermon transcript text here"
}
```
- Returns:
```json
{
    "content": "Generated content including devotional, summary, and discussion questions"
}
```

The generated content includes:
1. A 3-paragraph devotional with:
   - Relevant Bible verse
   - Closing prayer
2. A 1-paragraph summary
3. 5 small-group discussion questions

Example curl request:
```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"transcript": "Your sermon transcript here"}'
```

## Integration with Vercel Frontend

This backend is designed to work seamlessly with a Vercel frontend. CORS is configured to allow requests from:
- `http://localhost:3000` (local development)
- Your Vercel deployment domain

Make sure to update the CORS settings in `main.py` with your actual Vercel domain. 
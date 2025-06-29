from typing import Union, Literal
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
import os

app = FastAPI(title="Answering Machine API", version="1.0.0")

# Add startup logging
print("Starting Answering Machine API...")
print("FastAPI app created successfully")

# Try to import Google functionality
try:
    from google_calls import (
        gemini_text_call,
        gemini_audio_call,
        generate_gemini_stream,
        sanity_check,
        upload_file_to_gcs,
    )

    print("Google functionality imported successfully")
    GOOGLE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Google functionality not available: {e}")
    GOOGLE_AVAILABLE = False

# Try to import Twilio functionality
try:
    from twilio_calls import make_twilio_call

    print("Twilio functionality imported successfully")
    TWILIO_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Twilio functionality not available: {e}")
    TWILIO_AVAILABLE = False

# Update origins to include Cloud Run URLs
origins = [
    "http://localhost:3000",
    "http://192.168.86.77:3000",
    "https://*.run.app",  # Allow Cloud Run URLs
    "*",  # Allow all origins for development
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["POST", "GET", "PUT"],
    allow_headers=["*"],
)

print("CORS middleware added successfully")


@app.get("/")
async def root():
    """Health check endpoint"""
    print("Root endpoint called")
    return {"message": "Answering Machine API is running", "status": "healthy"}


@app.get("/health")
async def health_check():
    """Health check endpoint for Cloud Run"""
    print("Health check endpoint called")
    return {"status": "healthy", "service": "answering-machine-api"}


@app.get("/test")
async def test():
    """Simple test endpoint"""
    print("Test endpoint called")
    return {"message": "Test endpoint working"}


# Data models
class GeminiRequest(BaseModel):
    prompt: str
    model: Union[str, None] = None
    return_type: Union[Literal["text"], Literal["json"], None] = None


# Google Gemini endpoints (only if available)
if GOOGLE_AVAILABLE:

    @app.post("/sanity_check")
    def call_sanity_check(request: GeminiRequest):
        response = sanity_check(request.prompt)
        if not response:
            raise HTTPException(status_code=400, detail="Sanity check failed")
        return {"status": "sanity check passed"}

    @app.post("/gemini")
    def call_gemini(request: GeminiRequest):
        response = gemini_text_call(request.prompt)
        return {"prompt": request.prompt, "response": response}

    @app.post("/gemini/audio")
    def call_gemini_audio(request: GeminiRequest):
        response = gemini_audio_call(request.prompt)
        return Response(content=response, media_type="audio/mpeg")

    @app.post("/gemini/stream")
    async def gemini_stream(data: dict):
        prompt = data.get("prompt")
        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt is required")
        return Response(generate_gemini_stream(prompt))

    @app.post("/gcs/upload")
    async def call_upload_audio_file_to_gcs(file: UploadFile = File(...)):
        try:
            response = await upload_file_to_gcs(file)
            return response
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


# Twilio endpoints (only if available)
if TWILIO_AVAILABLE:

    @app.post("/twilio/call")
    async def call_make_twilio_call(to_phone_number: str, audio_file_url: str):
        response = await make_twilio_call(to_phone_number, audio_file_url)
        return Response(content=response, media_type="application/json")


print("All functionality loaded successfully")
print("Application startup complete")

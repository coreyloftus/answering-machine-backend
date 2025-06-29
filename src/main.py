from typing import Union, Literal
from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
from google_calls import (
    gemini_text_call,
    gemini_audio_call,
    generate_gemini_stream,
    sanity_check,
    upload_file_to_gcs,
)
from twilio_calls import make_twilio_call
from fastapi.middleware.cors import CORSMiddleware
from fastapi import HTTPException
from fastapi.responses import Response
import os

app = FastAPI(title="Answering Machine API", version="1.0.0")

# Add startup logging
print("Starting Answering Machine API...")
print(f"Environment variables loaded:")
print(f"  GEMINI_API_KEY: {'SET' if os.getenv('GEMINI_API_KEY') else 'NOT SET'}")
print(
    f"  SERVICE_ACCOUNT_KEY_JSON: {'SET' if os.getenv('SERVICE_ACCOUNT_KEY_JSON') else 'NOT SET'}"
)
print(
    f"  GCS_STORAGE_BUCKET: {'SET' if os.getenv('GCS_STORAGE_BUCKET') else 'NOT SET'}"
)
print(
    f"  TWILIO_ACCOUNT_SID: {'SET' if os.getenv('TWILIO_ACCOUNT_SID') else 'NOT SET'}"
)
print(f"  TWILIO_AUTH_TOKEN: {'SET' if os.getenv('TWILIO_AUTH_TOKEN') else 'NOT SET'}")
print(
    f"  TWILIO_PHONE_NUMBER: {'SET' if os.getenv('TWILIO_PHONE_NUMBER') else 'NOT SET'}"
)

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


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Answering Machine API is running", "status": "healthy"}


@app.get("/health")
async def health_check():
    """Health check endpoint for Cloud Run"""
    return {"status": "healthy", "service": "answering-machine-api"}


class GeminiRequest(BaseModel):
    prompt: str
    model: Union[str, None] = None
    return_type: Union[Literal["text"], Literal["json"], None] = None


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


@app.post("/twilio/call")
async def call_make_twilio_call(to_phone_number: str, audio_file_url: str):
    response = await make_twilio_call(to_phone_number, audio_file_url)
    return Response(content=response, media_type="application/json")

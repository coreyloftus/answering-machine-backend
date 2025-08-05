from typing import Union, Literal
from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
import os
from datetime import datetime
import secrets

app = FastAPI(title="Answering Machine API", version="1.0.0")

# Authentication setup
security = HTTPBearer()
API_KEY = os.getenv("RICK_ROLL_API_KEY")

# Generate a secure API key if none is provided (for development)
if not API_KEY:
    print(
        "⚠️  WARNING: No API_KEY environment variable found. Generating a temporary one for development."
    )
    API_KEY = secrets.token_urlsafe(32)
    print(f"🔑 Development API Key: {API_KEY}")
    print("   Add this to your frontend and environment variables!")


def verify_api_key(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> str:
    """
    Verify the API key from the Authorization header.
    Expected format: Authorization: Bearer <api_key>
    """
    if credentials.credentials != API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials


# Simple in-memory storage for call history (for tech demo purposes)
call_history = {}

# Add startup logging
print("Starting Answering Machine API...")
print("FastAPI app created successfully")

# Debug: Check if files exist
print(f"Current working directory: {os.getcwd()}")
print(f"Files in current directory: {os.listdir('.')}")
print(
    f"Files in src directory: {os.listdir('src') if os.path.exists('src') else 'src directory not found'}"
)

# Try to import Google functionality
try:
    print("Attempting to import google_calls...")
    from google_calls import (
        gemini_text_call,
        gemini_audio_call,
        generate_gemini_stream,
        sanity_check,
        upload_file_to_gcs,
        flowcode_demo_gemini_call,
    )

    print("Google functionality imported successfully")
    GOOGLE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Google functionality not available: {e}")
    print(f"Import error type: {type(e)}")
    print(f"Import error details: {str(e)}")
    GOOGLE_AVAILABLE = False
except Exception as e:
    print(f"Unexpected error importing Google functionality: {e}")
    print(f"Error type: {type(e)}")
    GOOGLE_AVAILABLE = False

# Try to import Twilio functionality
try:
    print("Attempting to import twilio_calls...")
    from twilio_calls import make_twilio_call, get_twilio_status, get_call_status

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


class TwilioCallRequest(BaseModel):
    to_phone_number: str
    audio_file_url: str


class CallRecord(BaseModel):
    call_sid: str
    to_phone_number: str
    audio_file_url: str
    status: str = "queued"
    created_at: datetime
    updated_at: datetime
    duration: str = None
    price: str = None
    error_message: str = None


# Google Gemini endpoints (only if available)
if GOOGLE_AVAILABLE:
    print("Registering Google endpoints...")

    @app.post("/sanity_check")
    def call_sanity_check(api_key: str = Depends(verify_api_key)):
        return {"status": True}

    @app.post("/gemini")
    def call_gemini(request: GeminiRequest, api_key: str = Depends(verify_api_key)):
        response = gemini_text_call(request.prompt)
        return {"prompt": request.prompt, "response": response}

    @app.post("/gemini/audio")
    def call_gemini_audio(
        request: GeminiRequest, api_key: str = Depends(verify_api_key)
    ):
        try:
            response = gemini_audio_call(request.prompt)
            if response is None:
                raise HTTPException(
                    status_code=500,
                    detail="Audio generation failed - no audio content returned",
                )
            return Response(content=response, media_type="audio/wav")
        except HTTPException:
            # Re-raise HTTPExceptions as-is
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Audio generation error: {str(e)}"
            )

    @app.post("/gemini/stream")
    async def gemini_stream(data: dict, api_key: str = Depends(verify_api_key)):
        prompt = data.get("prompt")
        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt is required")
        return generate_gemini_stream(prompt)

    @app.post("/gcs/upload")
    async def call_upload_audio_file_to_gcs(
        file: UploadFile = File(...), api_key: str = Depends(verify_api_key)
    ):
        try:
            response = await upload_file_to_gcs(file)
            return response
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/flowcode_demo")
    def call_flowcode_demo(
        request: GeminiRequest, api_key: str = Depends(verify_api_key)
    ):
        response = flowcode_demo_gemini_call(request.prompt)
        return response

    print("Google endpoints registered successfully")
else:
    print("Google endpoints NOT registered - functionality not available")


# Twilio endpoints (only if available)
if TWILIO_AVAILABLE:
    print("Registering Twilio endpoints...")

    @app.get("/twilio/status")
    def call_twilio_status(api_key: str = Depends(verify_api_key)):
        """Get Twilio account status and balance information"""
        response = get_twilio_status()
        return response

    @app.get("/twilio/call/{call_sid}/status")
    def get_twilio_call_status(call_sid: str, api_key: str = Depends(verify_api_key)):
        """Get status of a specific Twilio call"""
        # First check our local storage
        if call_sid in call_history:
            stored_call = call_history[call_sid]
            return {"success": True, "source": "local_storage", **stored_call}

        # Fall back to Twilio API
        response = get_call_status(call_sid)
        return response

    @app.post("/twilio/call/{call_sid}/status")
    async def handle_twilio_status_callback(
        call_sid: str,
        CallStatus: str = Form(...),
        CallDuration: str = Form(None),
        CallPrice: str = Form(None),
        ErrorMessage: str = Form(None),
        # Twilio sends many more fields, but these are the key ones
    ):
        """Handle Twilio status callback webhook - NO AUTH required as Twilio calls this directly"""
        print(f"📞 Callback received for call {call_sid}: {CallStatus}")

        # Update our stored call record
        if call_sid in call_history:
            call_history[call_sid].update(
                {
                    "status": CallStatus,
                    "updated_at": datetime.now().isoformat(),
                    "duration": CallDuration,
                    "price": CallPrice,
                    "error_message": ErrorMessage,
                }
            )
            print(f"✅ Updated call {call_sid} in storage")
        else:
            # This shouldn't happen, but let's handle it gracefully
            print(f"⚠️  Received callback for unknown call {call_sid}")

        # Return TwiML response (required by Twilio)
        return Response(content="<Response></Response>", media_type="application/xml")

    @app.get("/twilio/calls")
    def get_all_calls(api_key: str = Depends(verify_api_key)):
        """Get all calls from local storage (for tech demo purposes)"""
        return {
            "success": True,
            "calls": list(call_history.values()),
            "total_calls": len(call_history),
        }

    @app.post("/twilio/call")
    async def call_make_twilio_call(
        request: TwilioCallRequest, api_key: str = Depends(verify_api_key)
    ):
        # testing
        # print(f"Request received: {request}")
        # requestEcho = {
        #     "to_phone_number": request.to_phone_number,
        #     "audio_file_url": request.audio_file_url,
        # }
        # return requestEcho  # FastAPI automatically converts to JSON

        # actual call
        response = await make_twilio_call(
            request.to_phone_number, request.audio_file_url
        )

        # Store call information in our simple storage
        call_sid = response["call_sid"]
        now = datetime.now()
        call_history[call_sid] = {
            "call_sid": call_sid,
            "to_phone_number": request.to_phone_number,
            "audio_file_url": request.audio_file_url,
            "status": "queued",  # Initial status
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "duration": None,
            "price": None,
            "error_message": None,
        }

        print(f"📝 Stored call {call_sid} in local storage")
        return response

    print("Twilio endpoints registered successfully")
else:
    print("Twilio endpoints NOT registered - functionality not available")


print("All functionality loaded successfully")
print("Application startup complete")

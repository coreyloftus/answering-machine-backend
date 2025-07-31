import os
import json
import asyncio
import uuid
import wave
import io
from dotenv import load_dotenv
from fastapi import UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from google import genai
from google.genai import types

# from google.cloud import texttospeech
from google.oauth2 import service_account
from google.cloud import storage
import google.auth.transport.requests

load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY")
service_account_key_json = os.getenv("SERVICE_ACCOUNT_KEY_JSON")
gcs_storage_bucket = os.getenv("GCS_STORAGE_BUCKET")

# Add logging for debugging
print(f"GEMINI_API_KEY present: {bool(gemini_api_key)}")
print(f"SERVICE_ACCOUNT_KEY_JSON present: {bool(service_account_key_json)}")
print(f"GCS_STORAGE_BUCKET present: {bool(gcs_storage_bucket)}")


def create_wav_from_pcm(pcm_data, channels=1, rate=24000, sample_width=2):
    """Create WAV file data from PCM data following Google's recommended approach."""
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        wf.writeframes(pcm_data)
    return wav_buffer.getvalue()


def sanity_check(req: str):
    if not req:
        raise ValueError("Request cannot be empty")
    if len(req) > 4096:
        raise ValueError("Request exceeds maximum length of 4096 characters")
    return True


def get_google_credentials():
    """Get Google Cloud credentials from the environment variable."""
    if not service_account_key_json:
        print("WARNING: SERVICE_ACCOUNT_KEY_JSON is not set.")
        return None
    try:
        # Try to decode from base64 first (recommended approach)
        try:
            import base64

            decoded_json = base64.b64decode(service_account_key_json).decode("utf-8")
            service_account_info = json.loads(decoded_json)
            print("Using base64-decoded service account credentials.")
        except:
            # Fallback to direct JSON parsing
            service_account_info = json.loads(service_account_key_json)
            print("Using direct JSON service account credentials.")

        # Debug: Check if private_key exists and its format
        if "private_key" in service_account_info:
            private_key = service_account_info["private_key"]
            print(f"Private key length: {len(private_key)}")
            print(f"Private key starts with: {private_key[:50]}...")

            literal_newline = "\\n"
            actual_newline = chr(10)
            print(f"Contains literal \\n: {literal_newline in private_key}")
            print(f"Contains actual newlines: {actual_newline in private_key}")

            # Fix common issue: replace literal \n with actual newlines
            if literal_newline in private_key and actual_newline not in private_key:
                print("Fixing literal \\n characters in private key...")
                service_account_info["private_key"] = private_key.replace(
                    literal_newline, actual_newline
                )

        # Add Cloud Storage scopes
        credentials = service_account.Credentials.from_service_account_info(
            service_account_info,
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )

        # Debug service account info
        print("Successfully created service account credentials.")
        print(
            f"Service account email: {service_account_info.get('client_email', 'Not found')}"
        )
        print(f"Project ID: {service_account_info.get('project_id', 'Not found')}")
        print(
            f"Private key ID: {service_account_info.get('private_key_id', 'Not found')[:10]}..."
        )

        # Test credentials by refreshing them
        try:
            print("Testing credential refresh...")
            credentials.refresh(google.auth.transport.requests.Request())
            print("✅ Credentials refreshed successfully - JWT signature is valid!")
        except Exception as refresh_error:
            print(f"❌ Credential refresh failed: {refresh_error}")
            print(
                f"This confirms the JWT signature issue is in the service account key itself."
            )

        return credentials
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from SERVICE_ACCOUNT_KEY_JSON: {e}")
        return None
    except Exception as e:
        print(f"Error creating credentials: {e}")
        print(f"Error type: {type(e)}")
        return None


def gemini_text_call(
    prompt=None,
    model=None,
    return_type=None,
):
    if not gemini_api_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not configured")

    client = genai.Client(api_key=gemini_api_key)
    if not model:
        model = "gemini-2.0-flash"
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[f"{prompt}"],
    )
    print(response.text)
    return response


def flowcode_demo_gemini_call(prompt: str):
    if not gemini_api_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not configured")
    client = genai.Client(api_key=gemini_api_key)

    # Enhanced prompt to ensure clean JSON output
    enhanced_prompt = f"""
{prompt}

IMPORTANT: Respond with ONLY valid JSON. Do not include any markdown formatting, code blocks, or additional text. The response should be parseable directly by JSON.parse() in JavaScript.

Example of correct format:
{{"sentimentAnalysis": "frustrated", "sentimentBrief": "Customer is frustrated with payment issues", "category": "BILLING_ISSUE"}}

NOT like this:
```json
{{"sentimentAnalysis": "frustrated"}}
```
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash", contents=[enhanced_prompt]
        )
        text_json_reply = response.candidates[0].content.parts[0].text

        # Clean up the response to remove any markdown formatting
        cleaned_response = text_json_reply.strip()
        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response[7:]  # Remove ```json
        if cleaned_response.startswith("```"):
            cleaned_response = cleaned_response[3:]  # Remove ```
        if cleaned_response.endswith("```"):
            cleaned_response = cleaned_response[:-3]  # Remove trailing ```

        cleaned_response = cleaned_response.strip()

        # Validate that it's valid JSON
        try:
            json.loads(cleaned_response)
        except json.JSONDecodeError as e:
            print(f"Invalid JSON response: {e}")
            print(f"Raw response: {text_json_reply}")
            raise HTTPException(
                status_code=500, detail="Invalid JSON response from Gemini"
            )

        return cleaned_response
    except Exception as e:
        print(f"Error in flowcode_demo_gemini_call: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def gemini_audio_call(
    input_text=None,
):
    if not input_text:
        raise HTTPException(
            status_code=400, detail="Input text is required for audio generation"
        )

    try:
        # Initialize Gemini client
        client = genai.Client(api_key=gemini_api_key)

        # Generate audio using Gemini TTS
        response = client.models.generate_content(
            model="gemini-2.5-flash-preview-tts",
            contents=[input_text],
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name="Zephyr"
                        ),
                    ),
                ),
            ),
        )

        # Extract the audio data (this is raw PCM data)
        pcm_data = response.candidates[0].content.parts[0].inline_data.data

        print(f"Audio generation successful. PCM length: {len(pcm_data)} bytes")

        # Convert PCM to WAV format using Google's recommended approach
        wav_data = create_wav_from_pcm(pcm_data)
        print(f"WAV conversion successful. WAV length: {len(wav_data)} bytes")
        return wav_data

    except HTTPException:
        # Re-raise HTTPExceptions as-is
        raise
    except Exception as e:
        print(f"Error in gemini_audio_call: {e}")
        raise HTTPException(status_code=500, detail=f"Gemini TTS API error: {str(e)}")


def generate_gemini_stream(prompt: str):
    if not gemini_api_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not configured")
    client = genai.Client(api_key=gemini_api_key)
    model = client.models.generate_content_stream(
        model="gemini-2.0-flash",
        contents=[prompt],
    )

    async def event_stream():
        for chunk in model:
            if chunk.text:
                print(chunk.text)
            yield json.dumps({"data": chunk.text if chunk.text else ""})
            await asyncio.sleep(0.02)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


async def upload_file_to_gcs(file: UploadFile = File(...)):
    """Upload an audio file to Google Cloud Storage."""
    credentials = get_google_credentials()
    if not credentials:
        raise HTTPException(
            status_code=500, detail="Google Cloud credentials not configured"
        )

    if not gcs_storage_bucket:
        raise HTTPException(status_code=500, detail="GCS_STORAGE_BUCKET not configured")

    storage_client = storage.Client(credentials=credentials)

    # Debug storage client info
    print(f"Storage client project: {storage_client.project}")
    print(f"Target bucket name: {gcs_storage_bucket}")

    try:
        bucket = storage_client.bucket(gcs_storage_bucket)

        # Test bucket access
        print(f"Testing bucket access...")
        bucket.reload()  # This will fail if we don't have access
        print(f"Bucket location: {bucket.location}")
        print(f"Bucket project: {bucket.project_number}")

        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        blob = bucket.blob(unique_filename)

        blob.upload_from_file(file.file, content_type=file.content_type)
        print(
            f"File {file.filename} uploaded to gs://{gcs_storage_bucket}/{unique_filename}."
        )

        # Generate a signed URL for temporary access (expires in 1 hour)
        signed_url = blob.generate_signed_url(
            version="v4", expiration=3600, method="GET"  # 1 hour
        )

        response_data = {
            "message": "File uploaded successfully",
            "signed_url": signed_url,
            "file_name": unique_filename,
        }
        return response_data
    except Exception as e:
        print(f"Failed to access bucket {gcs_storage_bucket}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to upload file to GCS. {e}"
        )

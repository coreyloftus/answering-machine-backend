import os
import json
import asyncio
import uuid
from dotenv import load_dotenv
from fastapi import UploadFile, File, HTTPException
from google import genai
from google.cloud import texttospeech
from google.oauth2 import service_account
from google.cloud import storage

load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY")
service_account_key_json = os.getenv("SERVICE_ACCOUNT_KEY_JSON")
gcs_storage_bucket = os.getenv("GCS_STORAGE_BUCKET")

# Add logging for debugging
print(f"GEMINI_API_KEY present: {bool(gemini_api_key)}")
print(f"SERVICE_ACCOUNT_KEY_JSON present: {bool(service_account_key_json)}")
print(f"GCS_STORAGE_BUCKET present: {bool(gcs_storage_bucket)}")


def sanity_check(req: str):
    if not req:
        raise ValueError("Request cannot be empty")
    if not isinstance(req, str):
        raise TypeError("Request must be a string")
    if len(req) > 4096:
        raise ValueError("Request exceeds maximum length of 4096 characters")
    return True


def get_google_credentials():
    """Get Google Cloud credentials from the environment variable."""
    if not service_account_key_json:
        print("WARNING: SERVICE_ACCOUNT_KEY_JSON is not set.")
        return None
    try:
        service_account_info = json.loads(service_account_key_json)
        credentials = service_account.Credentials.from_service_account_info(
            service_account_info
        )
        print("Using service account credentials for Gemini API.")
        return credentials
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from SERVICE_ACCOUNT_KEY_JSON: {e}")
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

    # if return_type == "json":
    #     schema_text = """Please reply in a JSON format with a schema like this: \{project\}: \{scene\:\{line\:str, character\:str\}[]\}\}}"""

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
    voice_params="default",
    user_audio_pref="default",
):
    credentials = get_google_credentials()
    if credentials:
        client = texttospeech.TextToSpeechClient(credentials=credentials)
    else:
        print("no credentials provided, try again")
        return None
    systhesis_input = texttospeech.SynthesisInput(text=input_text)
    if voice_params == "default":
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US", ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
        )
    if user_audio_pref == "default":
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )
        print("Using default audio config: MP3 encoding")
    response = client.synthesize_speech(
        input=systhesis_input, voice=voice, audio_config=audio_config
    )
    if response.audio_content is None:
        print("No audio content returned from synthesis.")
        return None
    if response:
        print(response.audio_content[:10])
    return response.audio_content


async def generate_gemini_stream(prompt: str):
    if not gemini_api_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not configured")

    client = genai.Client(api_key=gemini_api_key)
    model = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[prompt],
        stream=True,
    )
    for chunk in model:
        yield {"data": chunk.text if chunk.text else ""}
        await asyncio.sleep(0.02)


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
    bucket_name = gcs_storage_bucket

    try:
        bucket = storage_client.bucket(bucket_name)

        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        blob = bucket.blob(unique_filename)

        blob.upload_from_file(file.file, content_type=file.content_type)
        print(f"File {file.filename} uploaded to gs://{bucket_name}/{unique_filename}.")

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
        print(f"Failed to access bucket {bucket_name}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to upload file to GCS. {e}"
        )

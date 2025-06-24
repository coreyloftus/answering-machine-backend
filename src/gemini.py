import os
import json
import asyncio
from dotenv import load_dotenv
from google import genai
from google.cloud import texttospeech
from google.oauth2 import service_account

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_VOICE_API_KEY_JSON = os.getenv("GEMINI_VOICE_API_KEY_JSON")


def sanity_check(req: str):
    if not req:
        raise ValueError("Request cannot be empty")
    if not isinstance(req, str):
        raise TypeError("Request must be a string")
    if len(req) > 4096:
        raise ValueError("Request exceeds maximum length of 4096 characters")
    return True


def gemini_text_call(
    prompt=None,
    model=None,
    return_type=None,
):
    client = genai.Client(api_key=GEMINI_API_KEY)
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


def gemini_audio_call(
    input_text=None,
    voice_params="default",
    user_audio_pref="default",
):
    if not GEMINI_VOICE_API_KEY_JSON:
        print("ERROR:: GEMINI_VOICE_API_KEY_JSON is not set.")
        credentials = None
    else:
        try:
            service_account_info = json.loads(GEMINI_VOICE_API_KEY_JSON)
            credentials = service_account.Credentials.from_service_account_info(
                service_account_info
            )
            print("Using service account credentials for Gemini API.")
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from GEMINI_VOICE_API_KEY_JSON: {e}")
            credentials = None
    if credentials:
        client = texttospeech.TextToSpeechClient(credentials=credentials)
    else:
        print("no credentials provided, try again")
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
    client = genai.Client(api_key=GEMINI_API_KEY)
    model = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[prompt],
        stream=True,
    )
    for chunk in model:
        yield {"data": chunk.text if chunk.text else ""}
        await asyncio.sleep(0.02)

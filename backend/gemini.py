import os
from dotenv import load_dotenv
from google import genai
from google.cloud import texttospeech

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY2")

client = genai.Client(api_key=GEMINI_API_KEY)


def gemini_text_call(
    prompt=None,
    model=None,
    return_type=None,
):
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
    client = texttospeech.TextToSpeechClient()
    systhesis_input = texttospeech.SynthesisInput(text=input_text)
    if (voice_params== "default"):
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US", ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
        )
    if (user_audio_pref == "default"):
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )
    response = client.synthesize_speech(
        input=systhesis_input, voice=voice, audio_config=audio_config
    )
    return response.audio_content

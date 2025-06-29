import os
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse
from fastapi import HTTPException

account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_phone_number = os.getenv("TWILIO_PHONE_NUMBER")

# Add logging for debugging
print(f"TWILIO_ACCOUNT_SID present: {bool(account_sid)}")
print(f"TWILIO_AUTH_TOKEN present: {bool(auth_token)}")
print(f"TWILIO_PHONE_NUMBER present: {bool(twilio_phone_number)}")

# Only create client if credentials are available
if account_sid and auth_token:
    client = Client(account_sid, auth_token)
else:
    client = None
    print("WARNING: Twilio credentials not configured")


def generate_twiml_for_call(audio_file_url: str) -> str:
    """Generate TwiML for a call with a greeting and an audio file."""
    if audio_file_url is None or audio_file_url == "":
        raise ValueError("Audio file URL is not set. Please provide an audio_file_url.")
    response = VoiceResponse()
    response.play(audio_file_url)
    response.hangup()
    return str(response)


def make_twilio_call(to_phone_number: str, audio_file_url: str) -> str:
    """Make Twilio Phone call with the provided audio file URL."""
    if not client:
        raise HTTPException(status_code=500, detail="Twilio credentials not configured")

    if not to_phone_number:
        raise ValueError("To phone number is not set.")
    if not audio_file_url:
        raise ValueError("Audio File URL not set.")
    twiml_xml = generate_twiml_for_call(audio_file_url)
    try:
        call = client.calls.create(
            to=to_phone_number, from_=twilio_phone_number, twiml=twiml_xml
        )
        print(f"Call initiated with SID: {call.sid}")
    except Exception as e:
        print(f"Failed to initiate call: {e}")
        raise e
    return {
        "message": "Call initiated successfully",
        "call_sid": call.sid,
        "audio_file_url": audio_file_url,
    }

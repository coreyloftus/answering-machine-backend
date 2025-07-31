import os
import requests
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


def get_twilio_status():
    """Get Twilio account status and information"""
    try:
        account = client.api.v2010.accounts(account_sid).fetch()

        print(f"✓ Authentication successful!")
        print(f"Account Name: {account.friendly_name}")
        print(f"Account Status: {account.status}")
        print(f"Account Type: {account.type}")

        # Extract properties to match TypeScript interface exactly
        return {
            "auth_token": account.auth_token,
            "date_created": account.date_created,
            "date_updated": account.date_updated,
            "friendly_name": account.friendly_name,
            "owner_account_sid": account.owner_account_sid,
            "sid": account.sid,
            "status": account.status,
            "subresource_uris": account.subresource_uris,
            "type": account.type,
            "uri": account.uri,
        }
    except Exception as e:
        print(f"Failed to get account status: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch Twilio account status: {str(e)}"
        )


def generate_twiml_for_call(audio_file_url: str) -> str:
    """Generate TwiML for a call with a greeting and an audio file."""
    if audio_file_url is None or audio_file_url == "":
        raise ValueError("Audio file URL is not set. Please provide an audio_file_url.")
    response = VoiceResponse()
    response.play(audio_file_url)
    response.hangup()
    return str(response)


async def make_twilio_call(to_phone_number: str, audio_file_url: str) -> str:
    """Make Twilio Phone call with the provided audio file URL."""
    if not client:
        raise HTTPException(status_code=500, detail="Twilio credentials not configured")

    if not to_phone_number:
        raise ValueError("To phone number is not set.")
    if not audio_file_url:
        raise ValueError("Audio File URL not set.")
    twiml_xml = generate_twiml_for_call(audio_file_url)
    try:
        # Create the call without status_callback first
        call = client.calls.create(
            to=to_phone_number,
            from_=twilio_phone_number,
            twiml=twiml_xml,
        )

        # Now update the call with the status_callback that includes the call SID
        call = client.calls(call.sid).update(
            status_callback_method="POST",
            status_callback=f"{os.getenv('API_URL')}/twilio/call/{call.sid}/status",
        )

        print(f"Call initiated with SID: {call.sid}")
    except Exception as e:
        print(f"Failed to initiate call: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to initiate call",
        }
    return {
        "success": True,
        "message": "Call initiated successfully",
        "call_sid": call.sid,
        "audio_file_url": audio_file_url,
    }


def get_call_status(call_sid: str):
    """Get status of a specific Twilio call"""
    if not client:
        return {
            "success": False,
            "error": "Twilio credentials not configured",
            "message": "Cannot fetch call status - Twilio client not initialized",
        }

    try:
        call = client.calls(call_sid).fetch()
        return {
            "success": True,
            "call_sid": call.sid,
            "status": call.status,
            "direction": call.direction,
            "from_": call.from_,
            "to": call.to,
            "duration": call.duration,
            "price": call.price,
            "price_unit": call.price_unit,
            "date_created": (
                call.date_created.isoformat() if call.date_created else None
            ),
            "date_updated": (
                call.date_updated.isoformat() if call.date_updated else None
            ),
            "start_time": call.start_time.isoformat() if call.start_time else None,
            "end_time": call.end_time.isoformat() if call.end_time else None,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to fetch call status for {call_sid}",
        }

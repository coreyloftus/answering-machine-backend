import os
from google import genai
from dotenv import load_dotenv
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY2")
client = genai.Client(api_key=GEMINI_API_KEY)


def gemini_text_call(
    prompt="Please give me a cursory overview of using rhetoric in english writing.",
):
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[prompt],
    )
    print(response.text)
    return response.text

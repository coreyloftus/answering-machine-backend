import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)


def gemini_text_call(
    prompt=None,
    model=None,
    return_type=None,
):
    if not model:
        model = "gemini-2.0-flash"

    if return_type == "json":
        schema_text = """Please reply in a JSON format with a schema like this: \{project\}: \{scene\:\{line\:str, character\:str\}[]\}\}}"""

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[f"{schema_text} {prompt}"],
    )
    print(response.text)
    return response

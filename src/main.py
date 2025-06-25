from typing import Union, Literal
from fastapi import FastAPI
from pydantic import BaseModel
from gemini import (
    gemini_text_call,
    gemini_audio_call,
    generate_gemini_stream,
    sanity_check,
    upload_file_to_gcs,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi import HTTPException
from fastapi.responses import Response

app = FastAPI()

origins = ["http://localhost:3000", "http://192.168.86.77:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["POST", "GET", "PUT"],
    allow_headers=["*"],
)


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
async def call_upload_audio_file_to_gcs(file: bytes):
    response = await upload_file_to_gcs(file)
    return Response(content=response, media_type="application/json")

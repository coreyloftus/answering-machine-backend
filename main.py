from typing import Union
from fastapi import FastAPI
from pydantic import BaseModel
from gemini import gemini_text_call
from fastapi.middleware.cors import CORSMiddleware

import os
from dotenv import load_dotenv
load_dotenv()

app = FastAPI()

origins = ["http://localhost:3000", "http://192.168.86.77:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["POST", "GET", "PUT"],
    allow_headers=["*"],
)
class Item(BaseModel):
    name: str
    price: float
    is_offer: Union[bool, None] = None


@app.get("/")
def read_root() -> dict:
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": str(item_id), "q": q}


@app.put("/items/{item_id}")
def update_item(item_id: int, item: Item):
    return {"item_name": item.name, "item_id": item_id}


class GeminiRequest(BaseModel):
    prompt: str


@app.get("/test_api_key")
def test_api_key():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {"status": "error", "message": "API key not found"}
    else:
        return {"status": "ok"}

@app.post("/gemini")
def call_gemini(request: GeminiRequest):
    response = gemini_text_call(request.prompt)
    return {"prompt": request.prompt, "response": response}

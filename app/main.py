from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests

from app.routes.health import router as health_router

app = FastAPI(
    title="OX AI Backend",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)


@app.get("/")
def root():
    return {
        "message": "OX AI Backend Running"
    }


class ChatRequest(BaseModel):
    message: str


@app.post("/chat")
def chat(request: ChatRequest):
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "HammerAI/llama-3-lexi-uncensored:8b-q5_K_M",
                "prompt": request.message,
                "stream": False
            },
            timeout=120
        )

        data = response.json()

        return {
            "response": data["response"]
        }

    except Exception as e:
        return {
            "response": f"Error: {str(e)}"
        }

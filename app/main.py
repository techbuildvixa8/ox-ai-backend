from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests

from app import config
from app.db import init_db
from app.routes.health import router as health_router
from app.routes.auth import router as auth_router

app = FastAPI(
    title="OX AI Backend",
    version="0.1.0"
)

# Credentialed CORS cannot use "*"; allow the configured frontend origin so the
# session cookie is accepted on /auth/session etc.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[config.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(auth_router)


@app.on_event("startup")
def _startup() -> None:
    # Create the users table (and any future tables) on boot.
    init_db()


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

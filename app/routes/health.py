from fastapi import APIRouter
import requests

router = APIRouter()

@router.get("/health")
def health():
    return {
        "status": "online",
        "service": "ox-ai-backend"
    }

@router.get("/status")
def status():
    try:
        response = requests.get(
            "http://localhost:11434/api/tags",
            timeout=3
        )

        if response.status_code == 200:
            return {
                "frontend": "connected",
                "backend": "online",
                "ollama": "online"
            }

    except Exception:
        pass

    return {
        "frontend": "connected",
        "backend": "online",
        "ollama": "offline"
    }

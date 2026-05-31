from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
def health():
    return {
        "status": "online",
        "service": "ox-ai-backend"
    }

@router.get("/status")
def status():
    return {
        "frontend": "connected",
        "backend": "online",
        "ollama": "offline"
    }

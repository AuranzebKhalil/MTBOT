from fastapi import APIRouter
from datetime import datetime

router = APIRouter()

@router.get("/")
def health_check():
    return {
        "status": "online",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0"
    }

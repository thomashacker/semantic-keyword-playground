import logging
from fastapi import APIRouter
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    return {"status": "healthy"}


@router.get("/env_check")
async def env_check():
    return {
        "weaviate_url_set": bool(settings.weaviate_url),
        "weaviate_api_key_set": bool(settings.weaviate_api_key),
        "openai_api_key_set": bool(settings.openai_api_key),
        "cors_origins": settings.cors_origins_list,
    }

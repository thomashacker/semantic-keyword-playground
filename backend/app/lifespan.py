import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
import weaviate
from app.config import settings

logger = logging.getLogger(__name__)

_client: weaviate.WeaviateAsyncClient | None = None


async def get_weaviate_client() -> weaviate.WeaviateAsyncClient:
    global _client
    if _client is None:
        _client = weaviate.use_async_with_weaviate_cloud(
            cluster_url=settings.weaviate_url,
            auth_credentials=weaviate.auth.AuthApiKey(settings.weaviate_api_key),
            headers={"X-OpenAI-Api-Key": settings.openai_api_key},
        )
        await _client.connect()
        logger.info("Weaviate async client connected")
    return _client


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        await get_weaviate_client()
    except Exception as e:
        logger.warning(f"Could not connect to Weaviate on startup: {e}")
    yield
    # Shutdown
    global _client
    if _client is not None:
        await _client.close()
        logger.info("Weaviate client closed")
        _client = None

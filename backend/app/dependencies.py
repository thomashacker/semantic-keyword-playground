from fastapi import HTTPException, status
from app.lifespan import get_weaviate_client
import weaviate


async def get_client() -> weaviate.WeaviateAsyncClient:
    try:
        client = await get_weaviate_client()
        return client
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Weaviate client unavailable: {str(e)}",
        )

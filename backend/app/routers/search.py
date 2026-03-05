import logging
from fastapi import APIRouter, Depends, HTTPException, status
from app.models.search import DualSearchResponse, HybridSearchRequest, HybridSearchResponse, SearchRequest, VectorPoint
from app.services.search_service import dual_search, fetch_viz_data, hybrid_search
from app.dependencies import get_client
import weaviate

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/search", tags=["search"])

VALID_COLLECTIONS = {"Landmarks", "Movies", "Science", "Games", "Pokemon"}


@router.post("", response_model=DualSearchResponse)
async def search(request: SearchRequest, client: weaviate.WeaviateAsyncClient = Depends(get_client)):
    if request.collection not in VALID_COLLECTIONS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Collection '{request.collection}' not found. Valid collections: {sorted(VALID_COLLECTIONS)}",
        )
    try:
        result = await dual_search(client, request)
        return result
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}",
        )


@router.post("/hybrid", response_model=HybridSearchResponse)
async def search_hybrid(request: HybridSearchRequest, client: weaviate.WeaviateAsyncClient = Depends(get_client)):
    if request.collection not in VALID_COLLECTIONS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Collection '{request.collection}' not found. Valid collections: {sorted(VALID_COLLECTIONS)}",
        )
    try:
        return await hybrid_search(client, request)
    except Exception as e:
        logger.error(f"Hybrid search error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Hybrid search failed: {str(e)}",
        )


@router.get("/vectors", response_model=list[VectorPoint])
async def get_vectors(
    query: str,
    collection: str,
    limit: int = 5,
    client: weaviate.WeaviateAsyncClient = Depends(get_client),
):
    if collection not in VALID_COLLECTIONS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Collection '{collection}' not found. Valid collections: {sorted(VALID_COLLECTIONS)}",
        )
    try:
        return await fetch_viz_data(client.collections.get(collection), query, limit)
    except Exception as e:
        logger.error(f"Vectors error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Vector fetch failed: {str(e)}",
        )

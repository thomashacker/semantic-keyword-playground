import asyncio
import logging
import time
from typing import List, Optional, Tuple
import weaviate
from weaviate.classes.query import MetadataQuery
from app.models.search import BM25Result, DualSearchResponse, HybridResult, HybridSearchRequest, HybridSearchResponse, SearchRequest, SearchTiming, SemanticResult, VectorPoint

logger = logging.getLogger(__name__)

STOP_WORDS = {"a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "is", "it", "its", "be", "are", "was", "were", "has", "have", "had"}

# Map collection name to its "title" and "description" fields
COLLECTION_FIELD_MAP = {
    "Landmarks": {"title": "title", "description": "description"},
    "Movies": {"title": "title", "description": "plot"},
    "Science": {"title": "concept", "description": "explanation"},
    "Games": {"title": "title", "description": "description"},
    "Pokemon": {"title": "title", "description": "description"},
}


def _compute_query_terms(query: str) -> List[str]:
    return [w.lower() for w in query.split() if len(w) > 2 and w.lower() not in STOP_WORDS]


def _dedup_by_title(results: list) -> list:
    seen = set()
    deduped = []
    for r in results:
        key = r.title.lower()
        if key not in seen:
            seen.add(key)
            deduped.append(r)
    return deduped


def _pca_2d(vectors: List[List[float]]) -> Optional[List[Tuple[float, float]]]:
    """Project vectors to 2D using PCA. Returns None if fewer than 2 vectors."""
    try:
        import numpy as np
        if len(vectors) < 2:
            return None
        X = np.array(vectors, dtype=float)
        X -= X.mean(axis=0)
        cov = np.cov(X.T)
        if cov.ndim < 2:
            return [(float(X[i, 0]), 0.0) for i in range(len(X))]
        eigenvalues, eigenvectors = np.linalg.eigh(cov)
        # Take top 2 eigenvectors (highest eigenvalues)
        idx = np.argsort(eigenvalues)[::-1]
        components = eigenvectors[:, idx[:2]]
        projected = X @ components
        return [(float(projected[i, 0]), float(projected[i, 1])) for i in range(len(projected))]
    except Exception as e:
        logger.warning(f"PCA failed: {e}")
        return None


async def _bm25_search(collection, query: str, limit: int) -> Tuple[List[BM25Result], float]:
    start = time.perf_counter()
    try:
        response = await collection.query.bm25(
            query=query,
            limit=limit,
            return_metadata=MetadataQuery(score=True, explain_score=True),
        )
        elapsed = (time.perf_counter() - start) * 1000
        results = []
        for obj in response.objects:
            props = obj.properties
            col_name = collection.name
            field_map = COLLECTION_FIELD_MAP.get(col_name, {"title": "title", "description": "description"})
            title = str(props.get(field_map["title"], ""))
            description = str(props.get(field_map["description"], ""))
            score = obj.metadata.score if obj.metadata and obj.metadata.score is not None else 0.0
            results.append(BM25Result(title=title, description=description, score=score, properties=dict(props)))
        return _dedup_by_title(results), elapsed
    except Exception as e:
        logger.error(f"BM25 search error: {e}")
        return [], (time.perf_counter() - start) * 1000


async def _semantic_search(collection, query: str, limit: int) -> Tuple[List[SemanticResult], float]:
    start = time.perf_counter()
    try:
        response = await collection.query.near_text(
            query=query,
            limit=limit,
            return_metadata=MetadataQuery(distance=True, certainty=True),
        )
        elapsed = (time.perf_counter() - start) * 1000
        results = []
        for obj in response.objects:
            props = obj.properties
            col_name = collection.name
            field_map = COLLECTION_FIELD_MAP.get(col_name, {"title": "title", "description": "description"})
            title = str(props.get(field_map["title"], ""))
            description = str(props.get(field_map["description"], ""))
            distance = obj.metadata.distance if obj.metadata else None
            certainty = obj.metadata.certainty if obj.metadata else None
            results.append(SemanticResult(
                title=title,
                description=description,
                distance=distance,
                certainty=certainty,
                properties=dict(props),
            ))
        return _dedup_by_title(results), elapsed
    except Exception as e:
        logger.error(f"Semantic search error: {e}")
        return [], (time.perf_counter() - start) * 1000


async def fetch_viz_data(collection, query: str, limit: int) -> List[VectorPoint]:
    try:
        response = await collection.query.near_text(
            query=query,
            limit=limit,
            include_vector=True,
            return_metadata=MetadataQuery(certainty=True, distance=True),
        )
        col_name = collection.name
        field_map = COLLECTION_FIELD_MAP.get(col_name, {"title": "title", "description": "description"})
        raw_vectors = []
        points_meta = []
        for obj in response.objects:
            props = obj.properties
            title = str(props.get(field_map["title"], ""))
            certainty = obj.metadata.certainty if obj.metadata else None
            distance = obj.metadata.distance if obj.metadata else None
            country = str(props["country"]) if "country" in props else None
            vec = obj.vector.get("default") if obj.vector else None
            raw_vectors.append(vec)
            points_meta.append({"title": title, "certainty": certainty, "distance": distance, "country": country})

        valid_vecs = [v for v in raw_vectors if v is not None]
        coords = _pca_2d(valid_vecs) if len(valid_vecs) >= 2 else None

        results = []
        for i, meta in enumerate(points_meta):
            coord = coords[i] if coords and raw_vectors[i] is not None else None
            if coord is None:
                continue
            results.append(VectorPoint(
                title=meta["title"],
                vector_2d=coord,
                certainty=meta["certainty"],
                distance=meta["distance"],
                country=meta["country"],
            ))
        return results
    except Exception as e:
        logger.error(f"Viz data fetch error: {e}")
        return []


async def hybrid_search(client: weaviate.WeaviateAsyncClient, request: HybridSearchRequest) -> HybridSearchResponse:
    collection = client.collections.get(request.collection)
    start = time.perf_counter()
    try:
        response = await collection.query.hybrid(
            query=request.query,
            alpha=request.alpha,
            limit=request.limit,
            return_metadata=MetadataQuery(score=True, distance=True, certainty=True),
        )
    except Exception as e:
        logger.error(f"Hybrid search error: {e}")
        return HybridSearchResponse(
            query=request.query,
            collection=request.collection,
            results=[],
            alpha=request.alpha,
            hybrid_ms=(time.perf_counter() - start) * 1000,
        )
    elapsed = (time.perf_counter() - start) * 1000
    field_map = COLLECTION_FIELD_MAP.get(request.collection, {"title": "title", "description": "description"})
    results = [
        HybridResult(
            title=str(obj.properties.get(field_map["title"], "")),
            description=str(obj.properties.get(field_map["description"], "")),
            score=obj.metadata.score if obj.metadata else None,
            certainty=obj.metadata.certainty if obj.metadata else None,
            distance=obj.metadata.distance if obj.metadata else None,
            properties=dict(obj.properties),
        )
        for obj in response.objects
    ]
    return HybridSearchResponse(
        query=request.query,
        collection=request.collection,
        results=_dedup_by_title(results),
        alpha=request.alpha,
        hybrid_ms=elapsed,
    )


async def dual_search(client: weaviate.WeaviateAsyncClient, request: SearchRequest) -> DualSearchResponse:
    collection = client.collections.get(request.collection)

    (bm25_results, bm25_ms), (semantic_results, semantic_ms) = await asyncio.gather(
        _bm25_search(collection, request.query, request.limit),
        _semantic_search(collection, request.query, request.limit),
    )

    query_terms = _compute_query_terms(request.query)

    return DualSearchResponse(
        query=request.query,
        collection=request.collection,
        bm25=bm25_results,
        semantic=semantic_results,
        timing=SearchTiming(bm25_ms=bm25_ms, semantic_ms=semantic_ms),
        query_terms=query_terms,
    )

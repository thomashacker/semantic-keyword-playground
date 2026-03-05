import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.models.search import BM25Result, SemanticResult, SearchTiming, DualSearchResponse


@pytest.mark.asyncio
async def test_search_empty_query_returns_422(client):
    """Empty query (min_length=1 violated) should return 422."""
    response = await client.post(
        "/search",
        json={"query": "", "collection": "Landmarks", "limit": 5},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_search_unknown_collection_returns_404(client):
    """Unknown collection should return 404."""
    response = await client.post(
        "/search",
        json={"query": "test", "collection": "UnknownCollection", "limit": 5},
    )
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_search_response_has_required_keys(client):
    """Search response must have bm25, semantic, timing, query, collection."""
    mock_response = DualSearchResponse(
        query="landmark in France",
        collection="Landmarks",
        bm25=[
            BM25Result(
                title="Arc de Triomphe",
                description="Iconic triumphal arch at the western end of the Champs-Élysées.",
                score=2.5,
                properties={"country": "France"},
            )
        ],
        semantic=[
            SemanticResult(
                title="Eiffel Tower",
                description="Iron lattice tower built in 1889, symbol of Paris.",
                distance=0.18,
                certainty=0.91,
                properties={"country": "France"},
            )
        ],
        timing=SearchTiming(bm25_ms=14.0, semantic_ms=52.0),
    )

    with patch("app.routers.search.dual_search", return_value=mock_response):
        response = await client.post(
            "/search",
            json={"query": "landmark in France", "collection": "Landmarks", "limit": 5},
        )

    assert response.status_code == 200
    data = response.json()
    assert "bm25" in data
    assert "semantic" in data
    assert "timing" in data
    assert "query" in data
    assert "collection" in data
    assert isinstance(data["bm25"], list)
    assert isinstance(data["semantic"], list)
    assert data["timing"]["bm25_ms"] > 0
    assert data["timing"]["semantic_ms"] > 0


@pytest.mark.asyncio
async def test_search_bm25_result_structure(client):
    """BM25 results must have title, description, score."""
    mock_response = DualSearchResponse(
        query="test",
        collection="Landmarks",
        bm25=[
            BM25Result(
                title="Eiffel Tower",
                description="Iron lattice tower.",
                score=1.5,
                properties={},
            )
        ],
        semantic=[],
        timing=SearchTiming(bm25_ms=10.0, semantic_ms=20.0),
    )

    with patch("app.routers.search.dual_search", return_value=mock_response):
        response = await client.post(
            "/search",
            json={"query": "test", "collection": "Landmarks", "limit": 5},
        )

    assert response.status_code == 200
    data = response.json()
    assert len(data["bm25"]) == 1
    result = data["bm25"][0]
    assert "title" in result
    assert "description" in result
    assert "score" in result
    assert result["title"] == "Eiffel Tower"
    assert result["score"] == 1.5


@pytest.mark.asyncio
async def test_search_semantic_result_structure(client):
    """Semantic results must have title, description, certainty, distance."""
    mock_response = DualSearchResponse(
        query="test",
        collection="Landmarks",
        bm25=[],
        semantic=[
            SemanticResult(
                title="Eiffel Tower",
                description="Iron lattice tower.",
                distance=0.18,
                certainty=0.91,
                properties={},
            )
        ],
        timing=SearchTiming(bm25_ms=10.0, semantic_ms=50.0),
    )

    with patch("app.routers.search.dual_search", return_value=mock_response):
        response = await client.post(
            "/search",
            json={"query": "test", "collection": "Landmarks", "limit": 5},
        )

    assert response.status_code == 200
    data = response.json()
    assert len(data["semantic"]) == 1
    result = data["semantic"][0]
    assert "title" in result
    assert "description" in result
    assert "certainty" in result
    assert "distance" in result
    assert result["certainty"] == 0.91
    assert result["distance"] == 0.18


@pytest.mark.asyncio
async def test_search_valid_collections(client):
    """All three valid collections should be accepted (not 404)."""
    mock_response = DualSearchResponse(
        query="test",
        collection="Movies",
        bm25=[],
        semantic=[],
        timing=SearchTiming(bm25_ms=1.0, semantic_ms=1.0),
    )

    for collection in ["Landmarks", "Movies", "Science"]:
        mock_response_col = DualSearchResponse(
            query="test",
            collection=collection,
            bm25=[],
            semantic=[],
            timing=SearchTiming(bm25_ms=1.0, semantic_ms=1.0),
        )
        with patch("app.routers.search.dual_search", return_value=mock_response_col):
            response = await client.post(
                "/search",
                json={"query": "test", "collection": collection, "limit": 5},
            )
        # Should not be 404 (may be 200 or 500 if mock doesn't fully work, but not 404)
        assert response.status_code != 404, f"Collection {collection} returned 404"

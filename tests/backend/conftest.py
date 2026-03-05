import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock, patch


@pytest_asyncio.fixture
async def client():
    """
    Create an httpx AsyncClient pointed at the FastAPI app.
    We mock the Weaviate client so tests don't need real credentials.
    """
    # Mock the Weaviate client to avoid real connections
    mock_weaviate = AsyncMock()
    mock_weaviate.is_connected.return_value = True

    with patch("app.lifespan._client", mock_weaviate):
        with patch("app.lifespan.get_weaviate_client", return_value=AsyncMock(return_value=mock_weaviate)):
            from app.main import app
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                yield ac

import pytest


@pytest.mark.asyncio
async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_env_check_returns_booleans(client):
    response = await client.get("/env_check")
    assert response.status_code == 200
    data = response.json()
    assert "weaviate_url_set" in data
    assert "weaviate_api_key_set" in data
    assert "openai_api_key_set" in data
    assert "cors_origins" in data
    # Values should be booleans
    assert isinstance(data["weaviate_url_set"], bool)
    assert isinstance(data["weaviate_api_key_set"], bool)
    assert isinstance(data["openai_api_key_set"], bool)
    # cors_origins is a list
    assert isinstance(data["cors_origins"], list)

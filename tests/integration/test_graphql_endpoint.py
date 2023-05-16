import pytest
from httpx import AsyncClient

from core.config import settings


@pytest.mark.asyncio
async def test_get_graphql(client: AsyncClient):
    response = await client.get(f"{settings.API_STR}/graphql")

    assert response.status_code == 200

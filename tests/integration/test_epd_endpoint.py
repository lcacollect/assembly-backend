import pytest
from httpx import AsyncClient

from core.config import settings


@pytest.mark.asyncio
async def test_get_epds(client: AsyncClient, epds):
    query = """
        query {
            epds {
                edges {
                    node {
                        name
                        source
                        gwp {
                            a1a3
                        }
                    }
                }
                numEdges
            }
        }
    """

    response = await client.post(f"{settings.API_STR}/graphql", json={"query": query, "variables": None})

    assert response.status_code == 200
    data = response.json()

    assert not data.get("errors")
    assert set(data["data"]["epds"]["edges"][0]["node"].keys()) == {"name", "source", "gwp"}
    assert data["data"]["epds"]["numEdges"] != 0


@pytest.mark.asyncio
async def test_filter_epds(client: AsyncClient, epds):
    query = """
        query {
            epds(filters: {name: {contains: "0"}}) {
                edges {
                    node {
                        name
                    }
                }

            }
        }
    """

    response = await client.post(f"{settings.API_STR}/graphql", json={"query": query, "variables": None})

    assert response.status_code == 200
    data = response.json()

    assert not data.get("errors")
    assert "EPD 0" in data["data"]["epds"]["edges"][0]["node"]["name"]

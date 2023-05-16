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
                        category
                        source
                        gwpByPhases
                        gwp(phases: ["A1-A3", "C"])   
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
    assert sorted(data["data"]["epds"]["edges"], key=lambda x: x.get("node").get("name")) == [
        {
            "node": {
                "name": f"EPD {i}",
                "category": "My Category",
                "source": "Ökobau",
                "gwpByPhases": {"A1-A3": i * 10.0, "C": i * 10 + 2.0},
                "gwp": i * 20 + 2.0,
            }
        }
        for i in range(3)
    ]
    assert len(data["data"]["epds"]["edges"]) == 3
    assert data["data"]["epds"]["numEdges"] == 3
    # TODD - fix this test!


@pytest.mark.asyncio
async def test_filter_epds(client: AsyncClient, epds):
    query = """
        query {
            epds(filters: {name: {contains: "0"}}) {
                edges {
                    node {
                        name
                        category
                    }
                }

            }
        }
    """

    response = await client.post(f"{settings.API_STR}/graphql", json={"query": query, "variables": None})

    assert response.status_code == 200
    data = response.json()

    assert not data.get("errors")
    assert data["data"]["epds"]["edges"][0]["node"] == {
        "name": f"EPD 0",
        "category": "My Category",
    }


@pytest.mark.asyncio
async def test_epds_gwp_calculation(client: AsyncClient, epds):
    query = """
        query {
            epds {
                edges {
                    node {
                        name
                        gwp(phases: ["A1-A3", "C"]) 
                    }
                }

            }
        }
    """

    response = await client.post(f"{settings.API_STR}/graphql", json={"query": query, "variables": None})

    assert response.status_code == 200
    data = response.json()

    assert not data.get("errors")
    sorted_data = sorted(data["data"]["epds"]["edges"], key=lambda x: x.get("node").get("name"))
    assert sorted_data[0]["node"] == {"name": f"EPD 0", "gwp": 2.0}

import json

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


@pytest.mark.asyncio
async def test_add_epds(client: AsyncClient, datafix_dir):
    query = """
        mutation ($epds: [GraphQLAddEpdInput!]!) {
            addEpds(epds: $epds) {
                id
                name
            }
        }
    """

    response = await client.post(
        f"{settings.API_STR}/graphql",
        json={
            "query": query,
            "variables": {
                "epds": [
                    {
                        "id": epd["id"],
                        "name": epd["name"],
                        "version": epd["version"],
                        "declaredUnit": epd["declaredUnit"],
                        "validUntil": epd["validUntil"].split("T")[0],
                        "publishedDate": epd["publishedDate"].split("T")[0],
                        "source": epd["source"],
                        "location": epd["location"],
                        "subtype": epd["subtype"],
                        "referenceServiceLife": epd["referenceServiceLife"],
                        "comment": epd["comment"],
                        "gwp": epd["gwp"],
                        "odp": epd["odp"],
                        "ap": epd["ap"],
                        "ep": epd["ep"],
                        "pocp": epd["pocp"],
                        "penre": epd["penre"],
                        "pere": epd["pere"],
                        "metaData": epd.get("metaData"),
                        "conversions": epd["conversions"],
                    }
                    for epd in json.loads((datafix_dir / "epds.json").read_text())
                ]
            },
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert not data.get("errors")
    assert data["data"]["addEpds"] != 0


@pytest.mark.asyncio
async def test_delete_epds(client: AsyncClient, epds):
    query = """
        mutation ($ids: [String!]!) {
            deleteEpds(ids: $ids)
        }
    """

    response = await client.post(
        f"{settings.API_STR}/graphql", json={"query": query, "variables": {"ids": [epds[0].id]}}
    )

    assert response.status_code == 200
    data = response.json()

    assert not data.get("errors")

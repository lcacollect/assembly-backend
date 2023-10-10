import pytest
from httpx import AsyncClient
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from core.config import settings
from models.assembly import Assembly


@pytest.mark.asyncio
async def test_get_assemblies(client: AsyncClient, assemblies):
    query = """
        query {
            assemblies {
                name
                category
                lifeTime
            }
        }
    """

    response = await client.post(f"{settings.API_STR}/graphql", json={"query": query, "variables": None})

    assert response.status_code == 200
    data = response.json()

    assert not data.get("errors")
    assert data["data"]["assemblies"] == [
        {"name": f"Assembly {i}", "category": "My Category", "lifeTime": 50.0} for i in range(3)
    ]


@pytest.mark.asyncio
async def test_get_assemblies_with_layers(client: AsyncClient, assembly_with_layers, project_id):
    query = """
        query {
            assemblies {
                name
                gwp
                layers {
                    name
                }
            }
        }
    """

    response = await client.post(f"{settings.API_STR}/graphql", json={"query": query, "variables": None})

    assert response.status_code == 200
    data = response.json()

    assert not data.get("errors")
    assert data["data"]["assemblies"][0] == {
        "name": f"Assembly {0}",
        "gwp": 10.0,
        "layers": [{"name": ""} for _ in range(2)],
    }


@pytest.mark.asyncio
async def test_create_assemblies(client: AsyncClient, project_exists_mock):
    mutation = """
        mutation ($assemblies: [AssemblyAddInput!]!) {
            addAssemblies(assemblies: $assemblies) {
                name
                category
                lifeTime
            }
        }
    """

    response = await client.post(
        f"{settings.API_STR}/graphql",
        json={
            "query": mutation,
            "variables": {
                "assemblies": [
                    {
                        "name": "My Assembly",
                        "category": "New Category",
                        "lifeTime": 45,
                        "description": "this is an assembly",
                        "unit": "m2",
                    }
                ]
            },
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert not data.get("errors")
    assert data["data"]["addAssemblies"][0] == {
        "name": f"My Assembly",
        "category": "New Category",
        "lifeTime": 45,
    }


@pytest.mark.asyncio
async def test_update_assemblies(client: AsyncClient, assemblies, project_exists_mock):
    assembly = assemblies[0]
    mutation = """
        mutation ($assemblies: [AssemblyUpdateInput!]!){
            updateAssemblies(assemblies: $assemblies) {
                name
                category
                lifeTime
            }
        }
    """

    response = await client.post(
        f"{settings.API_STR}/graphql",
        json={"query": mutation, "variables": {"assemblies": [{"id": assembly.id, "lifeTime": 40}]}},
    )

    assert response.status_code == 200
    data = response.json()

    assert not data.get("errors")
    assert data["data"]["updateAssemblies"][0] == {
        "name": assembly.name,
        "category": assembly.category,
        "lifeTime": 40,
    }


@pytest.mark.asyncio
async def test_delete_assemblies(client: AsyncClient, assemblies, db, project_exists_mock):
    assembly = assemblies[0]
    mutation = """
        mutation ($ids: [ID!]!){
            deleteAssemblies(ids: $ids)
        }
    """

    response = await client.post(
        f"{settings.API_STR}/graphql", json={"query": mutation, "variables": {"ids": [str(assembly.id)]}}
    )

    assert response.status_code == 200
    data = response.json()

    assert not data.get("errors")

    async with AsyncSession(db) as session:
        query = select(Assembly)
        _assemblies = await session.exec(query)
        _assemblies = _assemblies.all()

    assert len(_assemblies) == len(assemblies) - 1

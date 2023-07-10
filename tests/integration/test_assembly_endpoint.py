import pytest
from httpx import AsyncClient
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from core.config import settings
from models.assembly import Assembly


@pytest.mark.asyncio
async def test_get_assemblies(client: AsyncClient, assemblies, project_id):
    query = f"""
        query {{
            assemblies(projectId: "{project_id}") {{
                name
                category
                lifeTime
            }}
        }}
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
    query = f"""
        query {{
            assemblies(projectId: "{project_id}") {{
                name
                gwp
                layers {{
                    name
                }}
            }}
        }}
    """

    response = await client.post(f"{settings.API_STR}/graphql", json={"query": query, "variables": None})

    assert response.status_code == 200
    data = response.json()

    assert not data.get("errors")
    assert data["data"]["assemblies"][0] == {
        "name": f"Assembly {0}",
        "gwp": 30,
        "layers": [{"name": ""} for _ in range(3)],
    }


@pytest.mark.asyncio
async def test_create_assembly(client: AsyncClient):
    mutation = """
        mutation {
            addAssembly(name: "My Assembly", category: "New Category", lifeTime: 45, projectId: "TESTID", description: "this is an assembly", unit: m2) {
                name
                category
                lifeTime
            }
        }
    """

    response = await client.post(f"{settings.API_STR}/graphql", json={"query": mutation, "variables": None})

    assert response.status_code == 200
    data = response.json()

    assert not data.get("errors")
    assert data["data"]["addAssembly"] == {
        "name": f"My Assembly",
        "category": "New Category",
        "lifeTime": 45,
    }


@pytest.mark.asyncio
async def test_update_assembly(client: AsyncClient, assemblies):
    assembly = assemblies[0]
    mutation = f"""
        mutation {{
            updateAssembly(id: "{assembly.id}", lifeTime: 40) {{
                name
                category
                lifeTime
            }}
        }}
    """

    response = await client.post(f"{settings.API_STR}/graphql", json={"query": mutation, "variables": None})

    assert response.status_code == 200
    data = response.json()

    assert not data.get("errors")
    assert data["data"]["updateAssembly"] == {
        "name": assembly.name,
        "category": assembly.category,
        "lifeTime": 40,
    }


@pytest.mark.asyncio
async def test_delete_assembly(client: AsyncClient, assemblies, db):
    assembly = assemblies[0]
    mutation = f"""
        mutation {{
            deleteAssembly(id: "{assembly.id}")
        }}
    """

    response = await client.post(f"{settings.API_STR}/graphql", json={"query": mutation, "variables": None})

    assert response.status_code == 200
    data = response.json()

    assert not data.get("errors")

    async with AsyncSession(db) as session:
        query = select(Assembly)
        _assemblies = await session.exec(query)
        _assemblies = _assemblies.all()

    assert len(_assemblies) == len(assemblies) - 1

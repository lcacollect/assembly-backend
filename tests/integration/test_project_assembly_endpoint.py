import pytest
from httpx import AsyncClient
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from core.config import settings
from models.assembly import ProjectAssembly


@pytest.mark.asyncio
async def test_get_project_assemblies(client: AsyncClient, project_assemblies, project_id):
    query = f"""
        query {{
            projectAssemblies(projectId: "{project_id}") {{
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
    assert data["data"]["projectAssemblies"] == [
        {"name": f"Assembly {i}", "category": "My Category", "lifeTime": 50.0} for i in range(3)
    ]


@pytest.mark.asyncio
async def test_get_project_assemblies_with_layers(client: AsyncClient, project_assembly_with_layers, project_id):
    query = f"""
        query {{
            projectAssemblies(projectId: "{project_id}") {{
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
    assert data["data"]["projectAssemblies"][0] == {
        "name": f"Assembly {0}",
        "gwp": 30,
        "layers": [{"name": ""} for _ in range(3)],
    }


@pytest.mark.asyncio
async def test_create_project_assemblies(client: AsyncClient, project_exists_mock):
    mutation = """
        mutation ($assemblies: [ProjectAssemblyAddInput!]!) {
            addProjectAssemblies(assemblies: $assemblies) {
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
                        "projectId": "TESTID",
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
    assert data["data"]["addProjectAssemblies"][0] == {
        "name": f"My Assembly",
        "category": "New Category",
        "lifeTime": 45,
    }


@pytest.mark.asyncio
async def test_create_project_assemblies_from_assembly(
    client: AsyncClient, project_exists_mock, assembly_with_layers, project_id
):
    mutation = """
        mutation ($assemblies: [ID!]!, $projectId: ID!) {
            addProjectAssembliesFromAssemblies(assemblies: $assemblies, projectId: $projectId) {
                name
                category
                lifeTime
                projectId
                layers {
                    name
                    epd {
                        name
                    }
                    transportEpd {
                        name
                    }
                }
            }
        }
    """

    response = await client.post(
        f"{settings.API_STR}/graphql",
        json={
            "query": mutation,
            "variables": {"assemblies": [assembly_with_layers.id], "projectId": project_id},
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert not data.get("errors")
    assert data["data"]["addProjectAssembliesFromAssemblies"][0] == {
        "name": f"Assembly 0",
        "category": "My Category",
        "lifeTime": 50.0,
        "projectId": project_id,
        "layers": [
            {"name": "", "epd": {"name": "EPD 0"}, "transportEpd": {"name": "EPD 2"}},
            {"name": "", "epd": {"name": "EPD 1"}, "transportEpd": {"name": "EPD 2"}},
        ],
    }


@pytest.mark.asyncio
async def test_update_project_assemblies(client: AsyncClient, project_assemblies, project_exists_mock):
    assembly = project_assemblies[0]
    mutation = """
        mutation ($assemblies: [ProjectAssemblyUpdateInput!]!){
            updateProjectAssemblies(assemblies: $assemblies) {
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
    assert data["data"]["updateProjectAssemblies"][0] == {
        "name": assembly.name,
        "category": assembly.category,
        "lifeTime": 40,
    }


@pytest.mark.asyncio
async def test_delete_project_assemblies(client: AsyncClient, project_assemblies, db, project_exists_mock):
    assembly = project_assemblies[0]
    mutation = """
        mutation ($ids: [ID!]!){
            deleteProjectAssemblies(ids: $ids)
        }
    """

    response = await client.post(
        f"{settings.API_STR}/graphql", json={"query": mutation, "variables": {"ids": [str(assembly.id)]}}
    )

    assert response.status_code == 200
    data = response.json()

    assert not data.get("errors")

    async with AsyncSession(db) as session:
        query = select(ProjectAssembly)
        _assemblies = await session.exec(query)
        _assemblies = _assemblies.all()

    assert len(_assemblies) == len(project_assemblies) - 1

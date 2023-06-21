import pytest
from httpx import AsyncClient
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from core.config import settings
from models.epd import ProjectEPD


@pytest.mark.asyncio
async def test_get_project_epds(client: AsyncClient, project_epds, project_id):
    query = f"""
        query {{
            projectEpds(projectId: "{project_id}") {{
                name
                projectId
            }}
        }}
    """

    response = await client.post(f"{settings.API_STR}/graphql", json={"query": query, "variables": None})

    assert response.status_code == 200
    data = response.json()

    assert not data.get("errors")
    assert data["data"]["projectEpds"] == [
        {
            "name": f"EPD {i}",
            "projectId": project_id,
        }
        for i in range(3)
    ]


@pytest.mark.asyncio
async def test_filter_project_epds(client: AsyncClient, project_epds, project_id):
    query = f"""
        query {{
            projectEpds(projectId: "{project_id}", filters: {{name: {{contains: "0"}}}}) {{
                name
                projectId
            }}
        }}
    """

    response = await client.post(f"{settings.API_STR}/graphql", json={"query": query, "variables": None})

    assert response.status_code == 200
    data = response.json()

    assert not data.get("errors")
    assert len(data["data"]["projectEpds"]) == 1


@pytest.mark.asyncio
async def test_create_project_epd(client: AsyncClient, epds, project_id):
    mutation = f"""
        mutation {{
            addProjectEpd(projectId: "{project_id}", originId: "{epds[0].id}") {{
                name
                originId
                projectId
            }}
        }}
    """

    response = await client.post(f"{settings.API_STR}/graphql", json={"query": mutation, "variables": None})

    assert response.status_code == 200
    data = response.json()

    assert not data.get("errors")
    assert data["data"]["addProjectEpd"] == {
        "name": "EPD 0",
        "originId": epds[0].id,
        "projectId": project_id,
    }


@pytest.mark.asyncio
async def test_delete_project_epd(client: AsyncClient, project_epds, db):
    epd = project_epds[0]
    mutation = f"""
        mutation {{
            deleteProjectEpd(id: "{epd.id}")
        }}
    """

    response = await client.post(f"{settings.API_STR}/graphql", json={"query": mutation, "variables": None})

    assert response.status_code == 200
    data = response.json()

    assert not data.get("errors")

    async with AsyncSession(db) as session:
        query = select(ProjectEPD)
        epds = await session.exec(query)
        epds = epds.all()

    assert len(epds) == len(project_epds) - 1

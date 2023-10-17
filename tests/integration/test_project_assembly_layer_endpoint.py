import pytest
from httpx import AsyncClient
from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from core.config import settings
from models.assembly import ProjectAssembly


@pytest.mark.asyncio
async def test_add_project_assembly_layers(client: AsyncClient, project_assemblies, project_epds):
    assembly = project_assemblies[0]
    mutation = f"""
        mutation {{
            addProjectAssemblyLayers(
                id: "{assembly.id}"
                layers: [{', '.join([f'{{epdId: "{epd.id}", conversionFactor: 3, name: "Layer: {epd.name}"}}' for epd in project_epds])}]
            ) {{
                name
                conversionFactor
            }}
        }}
    """

    response = await client.post(f"{settings.API_STR}/graphql", json={"query": mutation, "variables": None})

    assert response.status_code == 200
    data = response.json()

    assert not data.get("errors")
    assert len(data["data"]["addProjectAssemblyLayers"]) == 3
    assert data["data"]["addProjectAssemblyLayers"][0] == {
        "name": "Layer: EPD 0",
        "conversionFactor": 3.0,
    }


@pytest.mark.asyncio
async def test_update_project_assembly_layers(client: AsyncClient, project_assembly_with_layers, project_epds):
    assembly = project_assembly_with_layers
    mutation = f"""
        mutation {{
            updateProjectAssemblyLayers(
                id: "{assembly.id}"
                layers: [{', '.join([
        f'{{id: "{layer.id}", epdId: "{layer.epd.id}", conversionFactor: 5, name: "{layer.epd.name}"}}' for layer in assembly.layers
    ])}]
            ) {{
                name
                epdId
                conversionFactor
            }}
        }}
    """

    response = await client.post(f"{settings.API_STR}/graphql", json={"query": mutation, "variables": None})

    assert response.status_code == 200
    data = response.json()

    assert not data.get("errors")
    assert sorted(data["data"]["updateProjectAssemblyLayers"], key=lambda x: x.get("name")) == [
        {"name": epd.name, "conversionFactor": 5.0, "epdId": epd.id} for epd in project_epds
    ]


@pytest.mark.asyncio
async def test_delete_project_assembly_layers(client: AsyncClient, project_assembly_with_layers, project_epds, db):
    assembly = project_assembly_with_layers
    mutation = """
        mutation deleteLayer($id: ID!, $layerId: ID!) {
            deleteProjectAssemblyLayers(
                id: $id
                layers: [$layerId ]
            )
        }
    """

    response = await client.post(
        f"{settings.API_STR}/graphql",
        json={
            "query": mutation,
            "variables": {"id": assembly.id, "layerId": assembly.layers[0].id},
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert not data.get("errors")

    async with AsyncSession(db) as session:
        query = (
            select(ProjectAssembly)
            .where(ProjectAssembly.id == assembly.id)
            .options(selectinload(ProjectAssembly.layers))
        )
        assembly = (await session.exec(query)).one()

    assert len(assembly.layers) == len(project_epds) - 1


@pytest.mark.asyncio
async def test_add_project_assembly_layers_with_transport(client: AsyncClient, project_assemblies, project_epds):
    assembly = project_assemblies[0]

    mutation = """
        mutation($id: ID!, $layers: [AssemblyLayerInput!]!) {
            addProjectAssemblyLayers(
                id: $id
                layers: $layers
            ) {
                name
                conversionFactor
                transportEpd {
                    name
                }
                transportDistance
            }
        }
    """

    response = await client.post(
        f"{settings.API_STR}/graphql",
        json={
            "query": mutation,
            "variables": {
                "id": assembly.id,
                "layers": [
                    {
                        "epdId": epd.id,
                        "conversionFactor": 3,
                        "name": f"Layer: {epd.name}",
                        "transportEpdId": project_epds[2].id,
                        "transportDistance": 30,
                    }
                    for epd in project_epds[:2]
                ],
            },
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert not data.get("errors")
    assert len(data["data"]["addProjectAssemblyLayers"]) == 2
    assert data["data"]["addProjectAssemblyLayers"][0] == {
        "name": "Layer: EPD 0",
        "conversionFactor": 3.0,
        "transportDistance": 30.0,
        "transportEpd": {"name": "EPD 2"},
    }

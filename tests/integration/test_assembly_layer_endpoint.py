import pytest
from httpx import AsyncClient
from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from core.config import settings
from models.assembly import Assembly


@pytest.mark.asyncio
async def test_add_assembly_layers(client: AsyncClient, assemblies, project_epds):
    assembly = assemblies[0]
    mutation = f"""
        mutation {{
            addAssemblyLayers(
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
    assert len(data["data"]["addAssemblyLayers"]) == 3
    assert data["data"]["addAssemblyLayers"][0] == {
        "name": "Layer: EPD 0",
        "conversionFactor": 3.0,
    }


@pytest.mark.asyncio
async def test_update_assembly_layers(client: AsyncClient, assembly_with_layers, project_epds):
    assembly = assembly_with_layers
    mutation = f"""
        mutation {{
            updateAssemblyLayers(
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
    assert sorted(data["data"]["updateAssemblyLayers"], key=lambda x: x.get("name")) == [
        {"name": epd.name, "conversionFactor": 5.0, "epdId": epd.id} for epd in project_epds
    ]


@pytest.mark.asyncio
async def test_delete_assembly_layers(client: AsyncClient, assembly_with_layers, project_epds, db):
    assembly = assembly_with_layers
    mutation = """
        mutation DeleteLayer($id: String!, $layerId: String!) {
            deleteAssemblyLayers(
                id: $id
                layers: [{id: $layerId} ]
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
        query = select(Assembly).where(Assembly.id == assembly.id).options(selectinload(Assembly.layers))
        assembly = (await session.exec(query)).one()

    assert len(assembly.layers) == len(project_epds) - 1

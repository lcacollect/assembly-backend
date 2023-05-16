import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from schema import schema


@pytest.mark.asyncio
async def test_get_assemblies(assemblies, db, project_id):
    query = f"""
        query {{
            assemblies(projectId: "{project_id}") {{
                name
                category
            }}
        }}
    """

    async with AsyncSession(db) as session:
        response = await schema.execute(query, context_value={"session": session, "user": True})

    assert response.errors is None
    assert response.data["assemblies"] == [
        {
            "name": f"Assembly {i}",
            "category": "My Category",
        }
        for i in range(3)
    ]


@pytest.mark.asyncio
async def test_create_assembly(db):
    mutation = """
        mutation {
            addAssembly(name: "My Assembly", category: "New Category", projectId: "TESTID", description: "this is an assembly") {
                name
                category
            }
        }
    """

    async with AsyncSession(db) as session:
        response = await schema.execute(mutation, context_value={"session": session, "user": True})

    assert response.errors is None
    assert response.data["addAssembly"] == {
        "name": f"My Assembly",
        "category": "New Category",
    }

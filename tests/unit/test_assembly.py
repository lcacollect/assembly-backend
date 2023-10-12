import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from schema import schema


@pytest.mark.asyncio
async def test_get_project_assemblies(project_assemblies, db, project_id):
    query = f"""
        query {{
            projectAssemblies(projectId: "{project_id}") {{
                name
                category
            }}
        }}
    """

    async with AsyncSession(db) as session:
        response = await schema.execute(query, context_value={"session": session, "user": True})

    assert response.errors is None
    assert sorted(response.data["projectAssemblies"], key=lambda x: x.get("name")) == [
        {
            "name": f"Assembly {i}",
            "category": "My Category",
        }
        for i in range(3)
    ]


@pytest.mark.asyncio
async def test_create_project_assemblies(db, project_exists_mock):
    mutation = """
        mutation ($assemblies: [ProjectAssemblyAddInput!]!) {
            addProjectAssemblies(assemblies: $assemblies) {
                name
                category
            }
        }
    """

    class MockUser:
        access_token = f"Bearer eydlhjaflkjadh"

    user = MockUser()

    async with AsyncSession(db) as session:
        response = await schema.execute(
            mutation,
            context_value={"session": session, "user": user},
            variable_values={
                "assemblies": [
                    {
                        "name": "My Assembly",
                        "category": "New Category",
                        "projectId": "TESTID",
                        "description": "this is an assembly",
                        "unit": "m2",
                    }
                ]
            },
        )

    assert response.errors is None
    assert response.data["addProjectAssemblies"][0] == {
        "name": f"My Assembly",
        "category": "New Category",
    }

from typing import Annotated, Optional

import httpx
import strawberry
from lcacollect_config.context import get_session, get_token
from sqlmodel import select
from strawberry.types import Info

import models.assembly as models_assembly
from core.config import settings
from exceptions import MicroServiceConnectionError, MicroServiceResponseError
from schema.assembly import GraphQLAssembly


async def get_assembly(info: Info, root: "GraphQLSchemaElement") -> GraphQLAssembly | None:
    """
    Fetches assembly of a schemaElement
    """
    if root.assembly_id:
        session = get_session(info)

        query = select(models_assembly.Assembly).where(models_assembly.Assembly.id == root.assembly_id)
        element = session.exec(query).first()
        if element:
            return GraphQLAssembly(
                name=element.name,
                project_id=element.project_id,
                category=element.category,
                life_time=element.life_time,
                description=element.description,
                conversion_factor=element.conversion_factor,
                meta_fields=element.meta_fields,
            )
    else:
        return None


@strawberry.federation.type(keys=["id"])
class GraphQLSchemaElement:
    id: strawberry.ID
    assembly_id: str | None = strawberry.federation.field(shareable=True)
    assembly: Optional[Annotated["GraphQLAssembly", strawberry.lazy("schema.assembly")]] = strawberry.field(
        resolver=get_assembly
    )

    @classmethod
    async def resolve_reference(cls, info: Info, id: strawberry.ID):
        return await get_elements([""], id, get_token(info))


async def get_elements(schemaCategories: list[str], id: str, token: str) -> GraphQLSchemaElement:
    query = """
        query getElements($schemaCategoryIds: [String!]!, $id: String){
            schemaElements(schemaCategoryIds: $schemaCategoryIds, elementId: $id) {
                id
                assemblyId
            }
        }
    """

    data = {}
    async with httpx.AsyncClient(
        headers={"authorization": f"Bearer {token}"},
    ) as client:
        response = await client.post(
            f"{settings.ROUTER_URL}/graphql",
            json={
                "query": query,
                "variables": {"schemaCategoryIds": schemaCategories, "id": id},
            },
        )
        if response.is_error:
            raise MicroServiceConnectionError(f"Could not receive data from {settings.ROUTER_URL}. Got {response.text}")
        data = response.json()
        if errors := data.get("errors"):
            raise MicroServiceResponseError(f"Got error from {settings.ROUTER_URL}: {errors}")

    element = data["data"]["schemaElements"][0]

    return GraphQLSchemaElement(id=element.get("id"), assembly_id=element.get("assemblyId"))

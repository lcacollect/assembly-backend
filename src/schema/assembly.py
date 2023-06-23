from typing import List, Optional

import strawberry
from lcacollect_config.context import get_session
from lcacollect_config.exceptions import DatabaseItemNotFound
from sqlalchemy.orm import selectinload
from sqlmodel import select
from strawberry.scalars import JSON
from strawberry.types import Info

import models.assembly as models_assembly
import models.links as models_links
import schema.assembly_layer as schema_assembly_layer


@strawberry.type
class GraphQLAssembly:
    id: str
    name: str
    category: str
    life_time: float
    meta_fields: JSON
    unit: str
    conversion_factor: float
    description: str

    layers: list[schema_assembly_layer.GraphQLAssemblyLayer]

    @strawberry.field
    def gwp(self, phases: list[str] | None = None) -> float:
        """Calculate the gwp of the assembly based on the underlying layers."""

        if self.layers:
            return sum([calculate_indicator(layer.epd.gwp, phases) * layer.conversion_factor for layer in self.layers])
        return 0


async def assemblies_query(info: Info, project_id: str) -> list[GraphQLAssembly]:
    session = get_session(info)

    query = select(models_assembly.Assembly).where(models_assembly.Assembly.project_id == project_id)
    if category_field := [field for field in info.selected_fields if field.name == "assemblies"]:
        if [field for field in category_field[0].selections if field.name in ["layers", "gwp"]]:
            query = query.options(
                selectinload(models_assembly.Assembly.layers).options(selectinload(models_links.AssemblyEPDLink.epd))
            )

    assemblies = await session.exec(query)

    return assemblies.all()


async def add_assembly_mutation(
    info: Info,
    name: str,
    category: str,
    project_id: str,
    description: str | None,
    life_time: float | None = 50,
    meta_fields: Optional[JSON] = None,
    conversion_factor: float | None = 1,
) -> GraphQLAssembly:
    if meta_fields is None:
        meta_fields = {}

    session = info.context.get("session")

    assembly = models_assembly.Assembly(
        name=name,
        project_id=project_id,
        category=category,
        life_time=life_time,
        description=description,
        conversion_factor=conversion_factor,
        meta_fields=meta_fields,
    )

    session.add(assembly)

    await session.commit()
    await session.refresh(assembly)
    query = select(models_assembly.Assembly).where(models_assembly.Assembly.id == assembly.id)
    if [field for field in info.selected_fields if field.name == "layers"]:
        query = query.options(
            selectinload(models_assembly.Assembly.layers).options(selectinload(models_links.AssemblyEPDLink.epd))
        )

    await session.exec(query)

    return assembly


async def update_assembly_mutation(
    info: Info,
    id: str,
    name: str | None = None,
    category: str | None = None,
    description: str | None = None,
    life_time: float | None = None,
    meta_fields: Optional[JSON] = None,
    conversion_factor: float | None = None,
) -> GraphQLAssembly:
    session = info.context.get("session")
    assembly = await session.get(models_assembly.Assembly, id)
    if not assembly:
        raise DatabaseItemNotFound(f"Could not find Assembly with id: {id}")

    kwargs = {
        "name": name,
        "category": category,
        "description": description,
        "life_time": life_time,
        "meta_fields": meta_fields,
        "conversion_factor": conversion_factor,
    }
    for key, value in kwargs.items():
        if value:
            setattr(assembly, key, value)

    session.add(assembly)

    await session.commit()
    await session.refresh(assembly)
    query = (
        select(models_assembly.Assembly)
        .where(models_assembly.Assembly.id == assembly.id)
        .options(selectinload(models_assembly.Assembly.layers).options(selectinload(models_links.AssemblyEPDLink.epd)))
    )
    await session.exec(query)
    return assembly


async def delete_assembly_mutation(info: Info, id: str) -> str:
    """Delete an Assembly"""

    session = info.context.get("session")
    assembly = await session.get(models_assembly.Assembly, id)

    await session.delete(assembly)
    await session.commit()
    return id


def calculate_indicator(data_by_phases: dict, phases: list[str] | None) -> float:
    if phases:
        return sum([data_by_phases.get(phase, 0) for phase in phases])
    else:
        return data_by_phases.get("a1a3", 0)

from typing import TYPE_CHECKING

import strawberry
from lcacollect_config.exceptions import DatabaseItemNotFound
from sqlalchemy.orm import selectinload
from sqlmodel import col, select
from strawberry.types import Info

import models.epd as models_epd
from models.links import ProjectAssemblyEPDLink
from graphql_types.assembly_layer import AssemblyLayerInput, GraphQLAssemblyLayer
from graphql_types.assembly_layer import AssemblyLayerUpdateInput
from models.assembly import ProjectAssembly

if TYPE_CHECKING:  # pragma: no cover
    pass


async def add_project_assembly_layers_mutation(
    info: Info,
    id: str,
    layers: list[AssemblyLayerInput],
) -> list[GraphQLAssemblyLayer]:
    session = info.context.get("session")
    assembly = await session.get(ProjectAssembly, id)
    if not assembly:
        raise DatabaseItemNotFound(f"Could not find Assembly with id: {id}")

    links = []
    for layer in layers:
        links.append(await add_layer_to_assembly(layer, assembly, session))
    await session.commit()

    return links


@strawberry.input
class AssemblyLayerDeleteInput:
    id: str


async def delete_project_assembly_layers_mutation(
    info: Info,
    id: str,
    layers: list[AssemblyLayerDeleteInput],
) -> list[str]:
    session = info.context.get("session")
    assembly = await session.get(ProjectAssembly, id)
    if not assembly:
        raise DatabaseItemNotFound(f"Could not find Assembly with id: {id}")

    deleted_epds = []

    for layer in layers:
        query = select(ProjectAssemblyEPDLink).where(
            ProjectAssemblyEPDLink.id == layer.id,
            ProjectAssemblyEPDLink.assembly_id == assembly.id,
        )
        link = (await session.exec(query)).one()
        await session.delete(link)
        deleted_epds.append(link.epd_id)

    await session.commit()
    return deleted_epds



async def update_project_assembly_layers_mutation(
    info: Info,
    id: str,
    layers: list[AssemblyLayerUpdateInput],
) -> list[GraphQLAssemblyLayer]:
    session = info.context.get("session")
    assembly = await session.get(ProjectAssembly, id)
    if not assembly:
        raise DatabaseItemNotFound(f"Could not find Assembly with id: {id}")

    epd_links = []
    for layer in layers:
        query = select(ProjectAssemblyEPDLink).where(
            ProjectAssemblyEPDLink.id == layer.id,
            ProjectAssemblyEPDLink.assembly_id == assembly.id,
        )
        link = (await session.exec(query)).one()
        kwargs = {
            "name": layer.name,
            "conversion_factor": layer.conversion_factor,
            "epd_id": layer.epd_id,
            "reference_service_life": layer.reference_service_life,
            "description": layer.description,
            "transport_type": layer.transport_type.value if layer.transport_type else None,
            "transport_distance": layer.transport_distance,
            "transport_unit": layer.transport_unit,
        }
        for key, value in kwargs.items():
            if value:
                setattr(link, key, value)

        session.add(link)
        epd_links.append(link)

    await session.commit()

    query = (
        select(ProjectAssemblyEPDLink)
        .where(col(ProjectAssemblyEPDLink.id).in_([layer.id for layer in layers]))
        .options(selectinload(ProjectAssemblyEPDLink.epd))
    )

    return (await session.exec(query)).all()


async def get_assembly_layers(layers: list[AssemblyLayerInput], session) -> list[models_epd.ProjectEPD]:
    """Get a list of ProjectEPD model objects, to be used as layers"""

    query = select(models_epd.ProjectEPD).where(col(models_epd.ProjectEPD.id).in_([layer.id for layer in layers]))

    epds = await session.exec(query)
    return epds.all()


async def add_layer_to_assembly(layer: AssemblyLayerInput, assembly, session) -> ProjectAssemblyEPDLink:
    """Add an EPD layer to an Assembly"""

    epd = await session.get(models_epd.ProjectEPD, layer.epd_id)
    if assembly.project_id != epd.project_id:
        raise AttributeError(
            f"Assembly projectId: {assembly.project_id} does not match epd's projectId: {epd.project_id}"
        )

    link = ProjectAssemblyEPDLink(
        assembly=assembly,
        assembly_id=assembly.id,
        epd=epd,
        epd_id=epd.id,
        conversion_factor=layer.conversion_factor,
        name=layer.name,
        description=layer.description,
        reference_service_life=layer.reference_service_life,
        transport_type=layer.transport_type.value if layer.transport_type else None,
        transport_distance=layer.transport_distance,
        transport_unit=layer.transport_unit,
    )
    session.add(link)

    return link

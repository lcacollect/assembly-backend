from typing import TYPE_CHECKING

import strawberry
from lcacollect_config.context import get_session
from lcacollect_config.exceptions import DatabaseItemNotFound
from sqlalchemy.orm import selectinload
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession
from strawberry import ID
from strawberry.types import Info

import models.epd as models_epd
from graphql_types.assembly_layer import (
    AssemblyLayerInput,
    AssemblyLayerUpdateInput,
    GraphQLAssemblyLayer,
)
from models.assembly import Assembly, ProjectAssembly
from models.links import AssemblyEPDLink, ProjectAssemblyEPDLink
from schema.epd import _mutation_add_project_epds_from_epds

if TYPE_CHECKING:  # pragma: no cover
    pass


async def add_assembly_layers_mutation(
    info: Info, id: ID, layers: list[AssemblyLayerInput]
) -> list[GraphQLAssemblyLayer]:
    """Add layers to an Assembly"""

    session = get_session(info)

    if info.field_name == "addProjectAssemblyLayers":
        assembly = await session.get(ProjectAssembly, id)
    elif info.field_name == "addAssemblyLayers":
        assembly = await session.get(Assembly, id)
    else:
        assembly = None

    if not assembly:
        raise DatabaseItemNotFound(f"Could not find Assembly with id: {id}")

    links = []
    for layer in layers:
        links.append(await add_layer_to_assembly(layer, assembly, session))
    await session.commit()

    return links


async def delete_assembly_layers_mutation(info: Info, id: ID, layers: list[ID]) -> list[str]:
    """Delete layers from an Assembly"""

    session = get_session(info)

    if info.field_name == "deleteProjectAssemblyLayers":
        assembly = await session.get(ProjectAssembly, id)
        link_model = ProjectAssemblyEPDLink
    elif info.field_name == "deleteAssemblyLayers":
        assembly = await session.get(Assembly, id)
        link_model = AssemblyEPDLink
    else:
        assembly = None
    if not assembly:
        raise DatabaseItemNotFound(f"Could not find Assembly with id: {id}")

    deleted_epds = []

    for layer_id in layers:
        query = select(link_model).where(
            link_model.id == layer_id,
            link_model.assembly_id == assembly.id,
        )
        link = (await session.exec(query)).one()
        await session.delete(link)
        deleted_epds.append(link.epd_id)

    await session.commit()
    return deleted_epds


async def update_assembly_layers_mutation(
    info: Info, id: ID, layers: list[AssemblyLayerUpdateInput]
) -> list[GraphQLAssemblyLayer]:
    session = get_session(info)

    if info.field_name == "updateProjectAssemblyLayers":
        assembly = await session.get(ProjectAssembly, id)
        link_model = ProjectAssemblyEPDLink
    elif info.field_name == "updateAssemblyLayers":
        assembly = await session.get(Assembly, id)
        link_model = AssemblyEPDLink
    else:
        assembly = None

    if not assembly:
        raise DatabaseItemNotFound(f"Could not find Assembly with id: {id}")

    epd_links = []
    for layer in layers:
        query = select(link_model).where(
            link_model.id == layer.id,
            link_model.assembly_id == assembly.id,
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
        select(link_model)
        .where(col(link_model.id).in_([layer.id for layer in layers]))
        .options(selectinload(link_model.epd))
    )

    return (await session.exec(query)).all()


async def get_assembly_layers(layers: list[AssemblyLayerInput], session) -> list[models_epd.ProjectEPD]:
    """Get a list of ProjectEPD model objects, to be used as layers"""

    query = select(models_epd.ProjectEPD).where(col(models_epd.ProjectEPD.id).in_([layer.id for layer in layers]))

    epds = await session.exec(query)
    return epds.all()


async def add_layer_to_assembly(
    layer: AssemblyLayerInput, assembly: ProjectAssembly | Assembly, session
) -> ProjectAssemblyEPDLink | AssemblyEPDLink:
    """Add an EPD layer to an Assembly"""

    epd_model = models_epd.ProjectEPD
    link_model = ProjectAssemblyEPDLink

    if isinstance(assembly, Assembly):
        epd_model = models_epd.EPD
        link_model = AssemblyEPDLink

    epd = await session.get(epd_model, layer.epd_id)
    if not epd:
        raise DatabaseItemNotFound(f"Could not find EPD with id: {layer.epd_id}")

    if isinstance(epd_model, models_epd.ProjectEPD) and assembly.project_id != epd.project_id:
        raise AttributeError(
            f"Assembly projectId: {assembly.project_id} does not match epd's projectId: {epd.project_id}"
        )

    link = link_model(
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


async def add_layers_to_project_assembly(assembly: ProjectAssembly, layers: AssemblyEPDLink, session: AsyncSession):
    """Add layers to a ProjectAssembly"""

    for layer in layers:
        epd = await session.get(models_epd.ProjectEPD, layer.epd_id)
        layer_input = AssemblyLayerInput(**layer.dict(exclude={"assembly_id"}))
        if not epd:
            _epd = await _mutation_add_project_epds_from_epds(session, [layer.epd_id], assembly.project_id)
            layer_input.epd_id = _epd[0].id

        await add_layer_to_assembly(layer_input, assembly, session)

    return assembly

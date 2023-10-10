from typing import TYPE_CHECKING, Type

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
        link_model = ProjectAssemblyEPDLink
    elif info.field_name == "addAssemblyLayers":
        assembly = await session.get(Assembly, id)
        link_model = AssemblyEPDLink
    else:
        assembly = None
        link_model = None

    if not assembly:
        raise DatabaseItemNotFound(f"Could not find Assembly with id: {id}")

    links = []
    for layer in layers:
        links.append(await add_layer_to_assembly(layer, assembly, session))
    await session.commit()

    category_field = [field for field in info.selected_fields if field.name == info.field_name]
    query = select(link_model).where(col(link_model.id).in_([layer.id for layer in links]))
    query = await assembly_layer_query_options(query, category_field, link_model)

    return (await session.exec(query)).all()


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
        link_model = None

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
            "transport_epd_id": layer.transport_epd_id if layer.transport_epd_id else None,
            "transport_distance": layer.transport_distance,
            "transport_conversion_factor": layer.transport_conversion_factor,
        }
        for key, value in kwargs.items():
            if value:
                setattr(link, key, value)

        session.add(link)
        epd_links.append(link)

    await session.commit()

    category_field = [field for field in info.selected_fields if field.name == info.field_name]
    query = select(link_model).where(col(link_model.id).in_([layer.id for layer in layers]))
    query = await assembly_layer_query_options(query, category_field, link_model)

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
    if layer.transport_epd_id:
        transport_epd = await session.get(epd_model, layer.transport_epd_id)
        if not transport_epd:
            raise DatabaseItemNotFound(f"Could not find EPD with id: {layer.transport_epd_id}")

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
        transport_epd_id=layer.transport_epd_id if layer.transport_epd_id else None,
        transport_distance=layer.transport_distance,
        transport_conversion_factor=layer.transport_conversion_factor,
    )
    session.add(link)

    return link


async def add_layers_to_project_assembly(assembly: ProjectAssembly, layers: AssemblyEPDLink, session: AsyncSession):
    """Add layers to a ProjectAssembly"""

    for layer in layers:
        epd = (
            await session.exec(
                select(models_epd.ProjectEPD).where(
                    models_epd.ProjectEPD.origin_id == layer.epd_id,
                    models_epd.ProjectEPD.project_id == assembly.project_id,
                )
            )
        ).first()
        layer_input = AssemblyLayerInput(**layer.dict(exclude={"assembly_id"}))
        if not epd:
            _epd = await _mutation_add_project_epds_from_epds(session, [layer.epd_id], assembly.project_id)
            layer_input.epd_id = _epd[0].id
        else:
            layer_input.epd_id = epd.id
        if layer.transport_epd_id:
            transport_epd = (
                await session.exec(
                    select(models_epd.ProjectEPD).where(
                        models_epd.ProjectEPD.origin_id == layer.transport_epd_id,
                        models_epd.ProjectEPD.project_id == assembly.project_id,
                    )
                )
            ).first()
            if not transport_epd:
                _epd = await _mutation_add_project_epds_from_epds(
                    session, [layer.transport_epd_id], assembly.project_id
                )
                layer_input.transport_epd_id = _epd[0].id
            else:
                layer_input.transport_epd_id = transport_epd.id

        await add_layer_to_assembly(layer_input, assembly, session)

    return assembly


async def assembly_layer_query_options(
    query,
    category_field,
    link_model: Type[AssemblyEPDLink | ProjectAssemblyEPDLink],
):
    if category_field:
        selections = [field for field in category_field[0].selections]
        if any(field.name == "epd" for field in selections):
            query = query.options(selectinload(link_model.epd))
        if any(field.name == "transportEpd" for field in selections):
            query = query.options(selectinload(link_model.transport_epd))

    return query

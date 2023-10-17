import logging
from typing import TYPE_CHECKING, Annotated, Type

import strawberry
from lcacollect_config.context import get_session
from lcacollect_config.exceptions import DatabaseItemNotFound
from lcacollect_config.graphql.input_filters import filter_model_query
from sqlalchemy.orm import selectinload
from sqlmodel import col, select
from strawberry import ID
from strawberry.types import Info

from core.validate import authenticate_project
from models.assembly import Assembly, ProjectAssembly
from models.links import AssemblyEPDLink, ProjectAssemblyEPDLink
from schema.assembly_layer import add_layers_to_project_assembly
from schema.inputs import AssemblyFilters

if TYPE_CHECKING:
    from graphql_types.assembly import (
        AssemblyAddInput,
        AssemblyUpdateInput,
        GraphQLAssembly,
        GraphQLProjectAssembly,
        ProjectAssemblyAddInput,
        ProjectAssemblyUpdateInput,
    )

logger = logging.getLogger(__name__)


async def assemblies_query(info: Info, filters: AssemblyFilters | None = None) -> list["GraphQLAssembly"]:
    """Get assemblies"""

    return await _query_assemblies(info, None, filters, Assembly, "assemblies")


async def project_assemblies_query(
    info: Info, project_id: str, filters: AssemblyFilters | None = None
) -> list["GraphQLProjectAssembly"]:
    """Get project assemblies"""

    return await _query_assemblies(info, project_id, filters, ProjectAssembly, "projectAssemblies")


async def _query_assemblies(
    info: Info,
    project_id: str | None,
    filters: AssemblyFilters | None,
    assembly_model: Type[Assembly | ProjectAssembly],
    _field: str,
) -> list["GraphQLProjectAssembly"] | list["GraphQLAssembly"]:
    """Abstracted function querying assemblies and project assemblies"""

    session = get_session(info)

    query = select(ProjectAssembly).where(ProjectAssembly.project_id == project_id).distinct(ProjectAssembly.id)
    link_model = ProjectAssemblyEPDLink
    if _field == "assemblies":
        query = select(Assembly).distinct(Assembly.id)
        link_model = AssemblyEPDLink

    category_field = [field for field in info.selected_fields if field.name == _field]
    query = await assembly_query_options(query, category_field, assembly_model, link_model)
    if filters:
        query = filter_model_query(assembly_model, filters, query=query)

    return (await session.exec(query)).all()


async def add_assemblies_mutation(
    info: Info, assemblies: list[Annotated["AssemblyAddInput", strawberry.lazy("graphql_types.assembly")]]
) -> list["GraphQLAssembly"]:
    """Add Assemblies"""

    return await _mutation_add_assemblies(info, assemblies, Assembly, "addAssemblies")


async def add_project_assemblies_mutation(
    info: Info, assemblies: list[Annotated["ProjectAssemblyAddInput", strawberry.lazy("graphql_types.assembly")]]
) -> list["GraphQLProjectAssembly"]:
    """Add Project Assemblies"""

    return await _mutation_add_assemblies(info, assemblies, ProjectAssembly, "addProjectAssemblies")


async def _mutation_add_assemblies(
    info: Info,
    assemblies: list["ProjectAssemblyAddInput"] | list["AssemblyAddInput"],
    assembly_model: Type[Assembly | ProjectAssembly],
    _field: str,
) -> list["GraphQLAssembly"] | list["GraphQLProjectAssembly"]:
    """Abstracted function for adding assemblies and project assemblies"""

    session = get_session(info)
    _assemblies = []

    for assembly_input in assemblies:
        data = {
            "name": assembly_input.name,
            "category": assembly_input.category,
            "life_time": assembly_input.life_time,
            "description": assembly_input.description,
            "conversion_factor": assembly_input.conversion_factor,
            "meta_fields": assembly_input.meta_fields if assembly_input.meta_fields is not None else {},
            "unit": assembly_input.unit.value if assembly_input.unit else None,
        }
        if assembly_model == ProjectAssembly:
            await authenticate_project(info, assembly_input.project_id)
            data["project_id"] = assembly_input.project_id
        elif assembly_model == Assembly:
            data["source"] = assembly_input.source or ""

        assembly = assembly_model(**data)

        session.add(assembly)
        _assemblies.append(assembly)
        logger.info(f"Adding {'project' if data.get('project_id') else ''} assembly with id: {assembly.id}")

    await session.commit()
    [await session.refresh(assembly) for assembly in _assemblies]

    category_field = [field for field in info.selected_fields if field.name == _field]
    query = select(assembly_model).where(col(assembly_model.id).in_([assembly.id for assembly in _assemblies]))

    query = await assembly_query_options(
        query,
        category_field,
        assembly_model,
        ProjectAssemblyEPDLink if assembly_model == ProjectAssembly else AssemblyEPDLink,
    )
    return (await session.exec(query)).all()


async def add_project_assemblies_from_assemblies_mutation(
    info: Info, assemblies: list[ID], project_id: ID
) -> list["GraphQLProjectAssembly"]:
    """Add Project Assemblies from Assemblies"""

    session = get_session(info)
    _assemblies = []
    await authenticate_project(info, project_id)

    for assembly_id in assemblies:
        query = select(Assembly).where(Assembly.id == assembly_id)
        query = query.options(selectinload(Assembly.layers).options(selectinload(AssemblyEPDLink.epd)))
        assembly = (await session.exec(query)).first()
        if not assembly:
            raise DatabaseItemNotFound(f"Could not find Assembly with id: {assembly_id}")

        project_assembly = ProjectAssembly.create_from_assembly(assembly, project_id)
        session.add(project_assembly)
        await add_layers_to_project_assembly(project_assembly, assembly.layers, session)

        _assemblies.append(project_assembly)
        logger.info(f"Adding project assembly with id: {project_assembly.id} from assembly with id: {assembly.id}")

        await session.commit()

    category_field = [field for field in info.selected_fields if field.name == "addProjectAssembliesFromAssemblies"]
    query = select(ProjectAssembly).where(col(ProjectAssembly.id).in_([assembly.id for assembly in _assemblies]))
    query = await assembly_query_options(
        query,
        category_field,
        ProjectAssembly,
        ProjectAssemblyEPDLink,
    )

    return (await session.exec(query)).all()


async def update_assemblies_mutation(
    info: Info, assemblies: list[Annotated["AssemblyUpdateInput", strawberry.lazy("graphql_types.assembly")]]
) -> list["GraphQLAssembly"]:
    """Update Assemblies"""

    return await _mutation_update_assemblies(info, assemblies, Assembly, "updateAssemblies")


async def update_project_assemblies_mutation(
    info: Info, assemblies: list[Annotated["ProjectAssemblyUpdateInput", strawberry.lazy("graphql_types.assembly")]]
) -> list["GraphQLProjectAssembly"]:
    """Update Project Assemblies"""

    return await _mutation_update_assemblies(info, assemblies, ProjectAssembly, "updateProjectAssemblies")


async def _mutation_update_assemblies(
    info: Info,
    assemblies: list["AssemblyUpdateInput"] | list["ProjectAssemblyUpdateInput"],
    assembly_model: Type[Assembly | ProjectAssembly],
    _field: str,
) -> list["GraphQLAssembly"] | list["GraphQLProjectAssembly"]:
    """Abstracted function for updating assemblies and project assemblies"""

    session = get_session(info)
    _assemblies = []

    for assembly_input in assemblies:
        assembly = await session.get(assembly_model, assembly_input.id)
        if not assembly:
            raise DatabaseItemNotFound(f"Could not find Assembly with id: {assembly_input.id}")

        kwargs = {
            "name": assembly_input.name,
            "category": assembly_input.category,
            "description": assembly_input.description,
            "life_time": assembly_input.life_time,
            "meta_fields": assembly_input.meta_fields,
            "conversion_factor": assembly_input.conversion_factor,
            "unit": assembly_input.unit.value if assembly_input.unit else None,
        }
        if assembly_model == Assembly:
            kwargs["source"] = assembly_input.source
        for key, value in kwargs.items():
            if value:
                setattr(assembly, key, value)

        session.add(assembly)
        logger.info(f"Updating project assembly with id: {assembly.id}")

    await session.commit()

    category_field = [field for field in info.selected_fields if field.name == _field]
    query = select(assembly_model).where(col(assembly_model.id).in_([assembly.id for assembly in assemblies]))
    query = await assembly_query_options(
        query,
        category_field,
        assembly_model,
        ProjectAssemblyEPDLink if assembly_model == ProjectAssembly else AssemblyEPDLink,
    )

    return (await session.exec(query)).all()


async def delete_assemblies_mutation(info: Info, ids: list[ID]) -> list[str]:
    """Delete Assemblies"""

    return await _mutation_delete_assemblies(info, ids, Assembly)


async def delete_project_assemblies_mutation(info: Info, ids: list[ID]) -> list[str]:
    """Delete Project Assemblies"""

    return await _mutation_delete_assemblies(info, ids, ProjectAssembly)


async def _mutation_delete_assemblies(
    info: Info, ids: list[str], assembly_model: Type[Assembly | ProjectAssembly]
) -> list[str]:
    """Abstracted function for deleting assemblies and project assemblies"""

    session = get_session(info)

    for _id in ids:
        logger.info(f"Deleting assembly with id: {_id}")
        assembly = await session.get(assembly_model, _id)
        await session.delete(assembly)

    await session.commit()
    return ids


async def assembly_query_options(
    query,
    category_field,
    assembly_model: Type[Assembly | ProjectAssembly],
    link_model: Type[AssemblyEPDLink | ProjectAssemblyEPDLink],
):
    if category_field:
        selections = [field for field in category_field[0].selections]
        if any(field.name == "gwp" for field in selections):
            query = query.options(selectinload(assembly_model.layers).options(selectinload(link_model.epd)))
        if layer_fields := [field for field in selections if field.name == "layers"]:
            layer_selections = [field for field in layer_fields[0].selections]
            if any(field.name == "epd" for field in layer_selections):
                query = query.options(selectinload(assembly_model.layers).options(selectinload(link_model.epd)))
            if any(field.name == "transportEpd" for field in layer_selections):
                query = query.options(
                    selectinload(assembly_model.layers).options(selectinload(link_model.transport_epd))
                )

    return query

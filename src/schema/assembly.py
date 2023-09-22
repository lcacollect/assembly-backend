import logging

from lcacollect_config.context import get_session
from lcacollect_config.exceptions import DatabaseItemNotFound
from sqlalchemy.orm import selectinload
from sqlmodel import select, col
from strawberry.types import Info

from core.validate import authenticate_project
from graphql_types.assembly import ProjectAssemblyUpdateInput, GraphQLProjectAssembly, ProjectAssemblyAddInput
from models.assembly import ProjectAssembly
from models.links import ProjectAssemblyEPDLink

logger = logging.getLogger(__name__)


async def project_assemblies_query(info: Info, project_id: str) -> list[GraphQLProjectAssembly]:
    """Get project assemblies"""

    session = get_session(info)

    category_field = [field for field in info.selected_fields if field.name == "projectAssemblies"]
    query = select(ProjectAssembly).where(ProjectAssembly.project_id == project_id)
    query = await assembly_query_options(query, category_field)

    return (await session.exec(query)).all()


async def add_project_assemblies_mutation(
    info: Info, assemblies: list[ProjectAssemblyAddInput]
) -> list[GraphQLProjectAssembly]:
    """Add Project Assemblies"""
    session = get_session(info)
    _assemblies = []

    for assembly_input in assemblies:
        await authenticate_project(info, assembly_input.project_id)

        assembly = ProjectAssembly(
            name=assembly_input.name,
            project_id=assembly_input.project_id,
            category=assembly_input.category,
            life_time=assembly_input.life_time,
            description=assembly_input.description,
            conversion_factor=assembly_input.conversion_factor,
            meta_fields=assembly_input.meta_fields if assembly_input.meta_fields is not None else {},
            unit=assembly_input.unit.value if assembly_input.unit else None,
        )

        session.add(assembly)
        _assemblies.append(assembly)
        logger.info(f"Adding project assembly with id: {assembly.id}")

    await session.commit()
    [await session.refresh(assembly) for assembly in _assemblies]

    category_field = [field for field in info.selected_fields if field.name == "addProjectAssemblies"]
    query = select(ProjectAssembly).where(col(ProjectAssembly.id).in_([assembly.id for assembly in _assemblies]))
    query = await assembly_query_options(query, category_field)
    return (await session.exec(query)).all()


async def update_project_assemblies_mutation(
    info: Info, assemblies: list[ProjectAssemblyUpdateInput]
) -> list[GraphQLProjectAssembly]:
    """Update Project Assemblies"""

    session = get_session(info)
    _assemblies = []
    for assembly_input in assemblies:
        assembly = await session.get(ProjectAssembly, assembly_input.id)
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
        for key, value in kwargs.items():
            if value:
                setattr(assembly, key, value)

        session.add(assembly)
        logger.info(f"Updating project assembly with id: {assembly.id}")

    await session.commit()

    category_field = [field for field in info.selected_fields if field.name == "updateProjectAssemblies"]
    query = select(ProjectAssembly).where(col(ProjectAssembly.id).in_([assembly.id for assembly in assemblies]))
    query = await assembly_query_options(query, category_field)

    return (await session.exec(query)).all()


async def delete_project_assemblies_mutation(info: Info, ids: list[str]) -> list[str]:
    """Delete Project Assemblies"""

    session = get_session(info)

    for _id in ids:
        logger.info(f"Deleting project assembly with id: {_id}")
        assembly = await session.get(ProjectAssembly, _id)
        await session.delete(assembly)

    await session.commit()
    return ids


async def assembly_query_options(query, category_field):
    if category_field and [field for field in category_field[0].selections if field.name in ["layers", "gwp"]]:
        return query.options(selectinload(ProjectAssembly.layers).options(selectinload(ProjectAssemblyEPDLink.epd)))
    return query

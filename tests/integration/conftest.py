from datetime import date

import pytest
from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from graphql_types.assembly_layer import AssemblyLayerInput
from models.assembly import Assembly, ProjectAssembly
from models.epd import EPD, ProjectEPD
from models.links import AssemblyEPDLink, ProjectAssemblyEPDLink
from schema.assembly_layer import add_layer_to_assembly


@pytest.fixture
async def project_assemblies(db, project_id) -> list[ProjectAssembly]:
    assemblies = []
    async with AsyncSession(db) as session:
        for i in range(3):
            assembly = ProjectAssembly(
                name=f"Assembly {i}",
                category="My Category",
                meta_fields={},
                project_id=project_id,
            )
            session.add(assembly)
            assemblies.append(assembly)
        await session.commit()
        [await session.refresh(assembly) for assembly in assemblies]

    yield assemblies


@pytest.fixture
async def assemblies(db, project_id) -> list[Assembly]:
    assemblies = []
    async with AsyncSession(db) as session:
        for i in range(3):
            assembly = Assembly(name=f"Assembly {i}", category="My Category", meta_fields={}, source="")
            session.add(assembly)
            assemblies.append(assembly)
        await session.commit()
        [await session.refresh(assembly) for assembly in assemblies]

    yield assemblies


@pytest.fixture
async def epds(db) -> list[EPD]:
    epds = []
    async with AsyncSession(db) as session:
        for i in range(3):
            impact_category = {
                "a1a3": i * 10,
                "a4": 0,
                "a5": 0,
                "b1": 0,
                "b2": 0,
                "b3": 0,
                "b4": 0,
                "b5": 0,
                "b6": 0,
                "b7": 0,
                "c1": i * 10 + 2,
                "c2": 0,
                "c3": 0,
                "c4": 0,
                "d": 0,
            }
            epd = EPD(
                name=f"EPD {i}",
                source="Ökobau",
                gwp=impact_category,
                odp=impact_category,
                ap=impact_category,
                ep=impact_category,
                pocp=impact_category,
                penre=impact_category,
                pere=impact_category,
                meta_fields={},
                conversions={},
                version="0.0.0",
                valid_until=date(year=1, month=1, day=1),
                published_date=date(year=1, month=1, day=2),
                location="DK",
                declared_unit="kg",
                subtype="Generic",
            )
            session.add(epd)
            epds.append(epd)

        await session.commit()
        [await session.refresh(epd) for epd in epds]

    yield epds


@pytest.fixture
async def project_epds(db, epds, project_id) -> list[ProjectEPD]:
    project_epds = []
    async with AsyncSession(db) as session:
        for epd in epds:
            project_epd = ProjectEPD.create_from_epd(epd, project_id=project_id)
            session.add(project_epd)
            project_epds.append(project_epd)
        await session.commit()
        [await session.refresh(epd) for epd in project_epds]

    yield project_epds


@pytest.fixture
async def project_assembly_with_layers(db, project_assemblies, project_epds) -> ProjectAssembly:
    assembly = project_assemblies[0]
    async with AsyncSession(db) as session:
        for epd in project_epds:
            await add_layer_to_assembly(
                AssemblyLayerInput(epd_id=epd.id, name="", conversion_factor=1),
                assembly,
                session,
            )

            await session.commit()
            await session.refresh(assembly)
        query = select(ProjectAssembly).where(ProjectAssembly.id == assembly.id)
        query = query.options(selectinload(ProjectAssembly.layers).options(selectinload(ProjectAssemblyEPDLink.epd)))

        assembly = (await session.exec(query)).first()

    yield assembly


@pytest.fixture
async def assembly_with_layers(db, assemblies, epds) -> Assembly:
    assembly = assemblies[0]
    async with AsyncSession(db) as session:
        for epd in epds[:2]:
            await add_layer_to_assembly(
                AssemblyLayerInput(epd_id=epd.id, name="", conversion_factor=1, transport_epd_id=epds[2].id),
                assembly,
                session,
            )

            await session.commit()
            await session.refresh(assembly)
        query = select(Assembly).where(Assembly.id == assembly.id)
        query = query.options(selectinload(Assembly.layers).options(selectinload(AssemblyEPDLink.epd)))

        assembly = (await session.exec(query)).first()

    yield assembly

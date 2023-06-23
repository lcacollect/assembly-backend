from datetime import date

import pytest
from lcacollect_config.connection import create_postgres_engine
from mixer.backend.sqlalchemy import Mixer
from sqlalchemy.orm import selectinload, sessionmaker
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from models.assembly import Assembly
from models.epd import EPD, ProjectEPD
from models.links import AssemblyEPDLink
from schema.assembly_layer import AssemblyLayerInput, add_layer_to_assembly


@pytest.fixture
async def assemblies(db, project_id) -> list[Assembly]:
    assemblies = []
    async with AsyncSession(db) as session:
        for i in range(3):
            assembly = Assembly(
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
async def epds(db) -> list[EPD]:
    session = sessionmaker(bind=create_postgres_engine(as_async=False))
    with session() as _session:
        mixer = Mixer(session=_session, commit=True)
        epds = mixer.cycle(3).blend(
            EPD,
            name=mixer.sequence(lambda n: f"EPD {n}"),
            source="Ökobau",
            gwp=mixer.sequence(lambda n: {"a1a3": n * 10, "c1": n * 10 + 2}),
            odp=mixer.sequence(lambda n: {"a1a3": n * 10, "c1": n * 10 + 2}),
            ap=mixer.sequence(lambda n: {"a1a3": n * 10, "c1": n * 10 + 2}),
            ep=mixer.sequence(lambda n: {"a1a3": n * 10, "c1": n * 10 + 2}),
            pocp=mixer.sequence(lambda n: {"a1a3": n * 10, "c1": n * 10 + 2}),
            penre=mixer.sequence(lambda n: {"a1a3": n * 10, "c1": n * 10 + 2}),
            pere=mixer.sequence(lambda n: {"a1a3": n * 10, "c1": n * 10 + 2}),
            meta_fields={},
            conversions={},
        )
        [_session.refresh(epd) for epd in epds]

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
async def assembly_with_layers(db, assemblies, project_epds) -> Assembly:
    assembly = assemblies[0]
    async with AsyncSession(db) as session:
        for epd in project_epds:
            await add_layer_to_assembly(
                AssemblyLayerInput(epd_id=epd.id, name="", conversion_factor=1),
                assembly,
                session,
            )

            await session.commit()
            await session.refresh(assembly)
        query = select(Assembly).where(Assembly.id == assembly.id)
        query = query.options(selectinload(Assembly.layers).options(selectinload(AssemblyEPDLink.epd)))

        assembly = (await session.exec(query)).first()

    yield assembly

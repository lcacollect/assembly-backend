from datetime import date

import pytest
from lcacollect_config.connection import create_postgres_engine
from pytest_alembic.config import Config
from sqlmodel.ext.asyncio.session import AsyncSession

from models.assembly import ProjectAssembly
from models.epd import EPD


@pytest.fixture
async def project_assemblies(db, project_id):
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
def epd(epds) -> EPD:
    yield epds[0]


@pytest.fixture
def alembic_config():
    """Override this fixture to configure the exact alembic context setup required."""
    yield Config()


@pytest.fixture
def alembic_engine(postgres):
    """Override this fixture to provide pytest-alembic powered tests with a database handle."""
    yield create_postgres_engine(as_async=False)

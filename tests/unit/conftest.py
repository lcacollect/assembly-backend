import pytest
from lcacollect_config.connection import create_postgres_engine
from sqlmodel import select
from pytest_alembic.config import Config
from sqlmodel.ext.asyncio.session import AsyncSession

from models.assembly import Assembly
from models.epd import EPD


@pytest.fixture
async def assemblies(db, project_id):
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

    yield assemblies


@pytest.fixture
async def epds(db, app) -> list[EPD]:
    async with AsyncSession(db) as session:
        query = select(EPD).limit(3)
        epds = (await session.exec(query)).all()

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

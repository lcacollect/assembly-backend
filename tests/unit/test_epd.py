import uuid
from datetime import date

import pytest
from asyncpg.exceptions import UniqueViolationError
from lcaconfig.connection import create_postgres_engine
from sqlalchemy.exc import IntegrityError
from sqlmodel.ext.asyncio.session import AsyncSession

from models.epd import EPD, ProjectEPD


def test_create_epd():
    epd = EPD(
        name="Test EPD",
        category="Test",
        gwp_by_phases={"A1": 10},
        odp_by_phases={"A1": 10},
        ap_by_phases={"A1": 10},
        ep_by_phases={"A1": 10},
        pocp_by_phases={"A1": 10},
        penre_by_phases={"A1": 10},
        pere_by_phases={"A1": 10},
        version="00.00.001",
        expiration_date=date(year=1, month=1, day=1),
        date_updated=date(year=1, month=1, day=2),
        source="Test",
        owner="Arkitema",
        region="Denmark",
        type="Generic",
        source_data="https://test.test",
    )

    assert epd


@pytest.mark.asyncio
async def test_create_project_epd_from_epd(epd):
    async with AsyncSession(create_postgres_engine()) as session:
        project_epd = ProjectEPD.create_from_epd(epd, project_id="testid123")
        session.add(project_epd)
        await session.commit()

    assert project_epd


@pytest.mark.parametrize("versions", [["00.00.01", "00.00.02"], ["00.00.01", "00.00.01"]])
@pytest.mark.asyncio
async def test_create_epds_with_versions(db, versions):
    origin_id = str(uuid.uuid4())
    epds = []

    async with AsyncSession(db) as session:
        for version in versions:
            epd = EPD(
                name="Test EPD",
                origin_id=origin_id,
                category="Test",
                gwp_by_phases={"A1": 10},
                odp_by_phases={"A1": 10},
                ap_by_phases={"A1": 10},
                ep_by_phases={"A1": 10},
                pocp_by_phases={"A1": 10},
                penre_by_phases={"A1": 10},
                pere_by_phases={"A1": 10},
                version=version,
                expiration_date=date(year=1, month=1, day=1),
                date_updated=date(year=1, month=1, day=2),
                source="Test",
                owner="Arkitema",
                region="Denmark",
                type="Generic",
                source_data="https://test.test",
                meta_fields={},
            )
            session.add(epd)
            epds.append(epd)
            if versions[0] == versions[1]:
                try:
                    await session.commit()
                except IntegrityError as exec_info:
                    assert isinstance(exec_info, IntegrityError)
            else:
                await session.commit()
        if versions[0] != versions[1]:
            [await session.refresh(epd) for epd in epds]

    if versions[0] != versions[1]:
        assert epds

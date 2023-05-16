import json

import pytest
from lcaconfig.connection import create_postgres_engine
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from import_data import ecoplatform, fetching
from models.epd import EPD


@pytest.mark.asyncio
async def test_ecoplatform_get_epd_ids(ecoplatform_token, mock_eco_get_epd_ids):
    result = await ecoplatform.get_epd_ids(count=1, token=ecoplatform_token)

    assert result
    assert result.get("count") > 1
    assert isinstance(result.get("data"), list)
    assert set(result["data"][0].keys()) == {
        "uid",
        "name",
        "version",
        "location",
        "type",
        "owner",
        "uri",
    }


@pytest.mark.asyncio
async def test_ecoplatform_get_epd_data(mock_eco_get_epd_data, ecoplatform_epd_url):
    result = await fetching.get_epd_data(url=ecoplatform_epd_url)

    assert result
    assert result == mock_eco_get_epd_data


def test_ecoplatform_parse_epd_data(datafix_dir):
    uid = "f256594a-a7bf-4bbb-91d0-65be256377c0"
    epd_data = json.loads((datafix_dir / f"{uid}.json").read_text())
    result = fetching.parse_epd_data(epd_data, {"source": "ECOPlatform", "type": "generic dataset"})

    assert result
    assert isinstance(result, EPD)


@pytest.mark.asyncio
async def test_ecoplatform_get_flow_dataset(datafix_dir, mock_eco_get_flow_dataset):
    uid = "f256594a-a7bf-4bbb-91d0-65be256377c0"
    epd_data = json.loads((datafix_dir / f"{uid}.json").read_text())

    data = await fetching.get_flow_dataset(epd_data, "https://epdireland.lca-data.com/resource")

    assert data
    assert isinstance(data, dict)


@pytest.mark.asyncio
async def test_ecoplatform_get_and_save_epd(db, mock_eco_get_epd_data, ecoplatform_epd_url, mock_eco_get_flow_dataset):
    await fetching.get_and_save_epd(
        ecoplatform_epd_url,
        data={"source": "ECOPlatform", "type": "generic dataset"},
        base_url="https://epdireland.lca-data.com/resource",
    )

    async with AsyncSession(create_postgres_engine()) as session:
        _epds = await session.exec(select(EPD))
        epds = _epds.all()

    assert epds
    assert epds[0]
    assert isinstance(epds[0], EPD)


@pytest.mark.asyncio
async def test_ecoplatform_import_data(
    db,
    ecoplatform_token,
    mock_eco_get_epd_data,
    mock_eco_get_epd_ids,
    mock_eco_get_flow_dataset,
):
    await ecoplatform.import_data(ecoplatform_token, 1)

    async with AsyncSession(create_postgres_engine()) as session:
        _epds = await session.exec(select(EPD))
        epds = _epds.all()

    assert epds

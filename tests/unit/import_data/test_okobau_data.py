import json

import pytest
from lcaconfig.connection import create_postgres_engine
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from import_data import fetching, okobau
from models.epd import EPD


@pytest.mark.asyncio
async def test_okobau_get_epd_count(mock_oko_get_number_of_epds):
    result = await okobau.get_number_of_epds()

    assert result
    assert isinstance(result, int)
    assert result > 1


@pytest.mark.asyncio
async def test_okobau_get_epd_ids(mock_oko_get_epd_ids):
    result = await okobau.get_epd_ids(count=1)

    assert result
    assert isinstance(result, list)
    assert set(result[0].keys()) == {
        "uid",
        "name",
        "version",
        "location",
        "type",
        "owner",
    }


@pytest.mark.asyncio
async def test_okobau_get_epd_data(mock_oko_get_epd_data, okobau_epd_url):
    result = await fetching.get_epd_data(url=okobau_epd_url)

    assert result
    assert result == mock_oko_get_epd_data


def test_okobau_parse_epd_data(datafix_dir):
    uid = "f63ac879-fa7d-4f91-813e-e816cbdf1927"
    epd_data = json.loads((datafix_dir / f"{uid}.json").read_text())
    result = fetching.parse_epd_data(epd_data, {"source": "Ökobau", "type": "generic dataset"})

    assert result
    assert isinstance(result, EPD)


@pytest.mark.parametrize(
    "uid,unit",
    [
        ("4e1beb5b-f059-4aa9-b12a-4462eb1fa606", "m3"),
        ("8fc69490-4aad-c4a4-9ecb-c9e76c97038e", "m2"),
    ],
)
def test_okobau_parse_flow_data(datafix_dir, uid, unit):
    flow_data = json.loads((datafix_dir / f"{uid}.json").read_text())
    result = fetching.parse_flow_data(flow_data)

    assert result
    assert isinstance(result, dict)
    assert set(result.keys()) == {"unit", "conversions"}
    assert result.get("unit") == unit


@pytest.mark.asyncio
async def test_okobau_get_flow_dataset_f63ac879(datafix_dir, mock_oko_get_flow_dataset_4e1beb5b):
    uid = "f63ac879-fa7d-4f91-813e-e816cbdf1927"
    epd_data = json.loads((datafix_dir / f"{uid}.json").read_text())

    data = await fetching.get_flow_dataset(epd_data, okobau.OKOBAU_URL)

    assert data
    assert isinstance(data, dict)


@pytest.mark.asyncio
async def test_okobau_get_flow_dataset_f83d4ab5(datafix_dir, mock_oko_get_flow_dataset_8fc69490):
    uid = "f83d4ab5-b65c-4cf1-b586-0942215c08ba"
    epd_data = json.loads((datafix_dir / f"{uid}.json").read_text())

    data = await fetching.get_flow_dataset(epd_data, okobau.OKOBAU_URL)

    assert data
    assert isinstance(data, dict)


@pytest.mark.asyncio
async def test_okobau_get_and_save_epd(db, mock_oko_get_epd_data, okobau_epd_url, mock_oko_get_flow_dataset_4e1beb5b):
    await fetching.get_and_save_epd(
        url=okobau_epd_url,
        data={"source": "Ökobau", "type": "generic dataset"},
        base_url=okobau.OKOBAU_URL,
    )

    async with AsyncSession(create_postgres_engine()) as session:
        _epds = await session.exec(select(EPD))
        epds = _epds.all()

    assert epds
    assert epds[0]
    assert isinstance(epds[0], EPD)


@pytest.mark.asyncio
async def test_okobau_get_and_save_duplicate_epd(
    db, mock_oko_get_epd_data, okobau_epd_url, mock_oko_get_flow_dataset_4e1beb5b
):
    await fetching.get_and_save_epd(
        url=okobau_epd_url,
        data={"source": "Ökobau", "type": "generic dataset"},
        base_url=okobau.OKOBAU_URL,
    )
    await fetching.get_and_save_epd(
        url=okobau_epd_url,
        data={"source": "Ökobau", "type": "specific dataset"},
        base_url=okobau.OKOBAU_URL,
    )

    async with AsyncSession(create_postgres_engine()) as session:
        _epds = await session.exec(select(EPD))
        epds = _epds.all()

    assert epds
    assert len(epds) == 1
    assert epds[0].type == "specific dataset"


@pytest.mark.asyncio
async def test_okobau_import_data(
    db,
    mock_oko_get_epd_data,
    mock_oko_get_epd_ids,
    mock_oko_get_number_of_epds,
    mock_oko_get_flow_dataset_4e1beb5b,
):
    await okobau.import_data(1)

    async with AsyncSession(create_postgres_engine()) as session:
        _epds = await session.exec(select(EPD))
        epds = _epds.all()

    assert epds

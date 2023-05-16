import logging

import httpx

import import_data.fetching as fetching

logger = logging.getLogger(__name__)

OKOBAU_URL = "https://oekobaudat.de/OEKOBAU.DAT/resource/datastocks/cd2bda71-760b-4fcc-8a0b-3877c10000a8"


async def get_epd_ids(count=500):
    logger.info(f"Fetching {count} ids from Ökobau server")

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{OKOBAU_URL}/processes?format=json&pageSize={count}")
        response.raise_for_status()

        data = response.json()

    _data = [
        {
            "uid": elem.get("uuid"),
            "name": elem.get("name"),
            "version": elem.get("version"),
            "location": elem.get("geo"),
            "type": elem.get("subType"),
            "owner": elem.get("owner"),
        }
        for elem in data.get("data")
    ]
    return _data


async def get_number_of_epds() -> int:
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{OKOBAU_URL}/processes?countOnly=true&format=json")
        response.raise_for_status()

        data = response.json()

    return data.get("totalCount")


async def import_data(limit=100):
    logger.info("Importing Ökobau EPDs")
    epd_count = await get_number_of_epds()
    logger.info(f"There is {epd_count} EPDs in the Ökobau database. Fetching {limit if limit < epd_count else 'all'}")

    epd_ids = await get_epd_ids(limit)

    logger.info("Starting fetching data")

    [
        await fetching.get_and_save_epd(
            url=f"{OKOBAU_URL}/processes/{data.get('uid')}?version={data.get('version')}",
            data={"source": "Ökobau", **data},
            base_url=OKOBAU_URL,
        )
        for data in epd_ids
    ]

    logger.info("Done processing data")

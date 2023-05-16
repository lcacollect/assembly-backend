import logging

import httpx

import import_data.fetching as fetching

logger = logging.getLogger(__name__)

ECOPLATFORM_URL = "https://data.eco-platform.org/resource"


async def get_epd_ids(token: str, start_index=0, count=500) -> dict:
    logger.info(f"Fetching {count} ids from ECO Platform server")

    async with httpx.AsyncClient(headers={"Authorization": f"Bearer {token}"}) as client:
        response = await client.get(
            f"{ECOPLATFORM_URL}/processes?"
            f"search=true&distributed=true&virtual=true&metaDataOnly=false"
            f"&format=json&startIndex={start_index}&pageSize={count}"
        )
        response.raise_for_status()

        data = response.json()

    _data = [
        {
            "uid": elem.get("uuid"),
            "name": elem.get("name"),
            "version": elem.get("version"),
            "uri": elem.get("uri"),
            "location": elem.get("geo"),
            "type": elem.get("subType"),
            "owner": elem.get("owner"),
        }
        for elem in data.get("data")
    ]
    return {"data": _data, "count": data.get("totalCount")}


async def import_data(token: str, limit=100):
    logger.info("Importing ECO Platform EPDs")

    start_index = 0
    data_size = 500
    count = limit or 500
    while start_index < count:
        _size = limit if limit < data_size else data_size
        data = await get_epd_ids(token, start_index, _size)
        count = data.get("count") if not limit and count <= limit else limit
        epd_ids = data.get("data")
        logger.info(
            f"There are {data.get('count')} EPDs in the ECO platform database. "
            f"Fetching {start_index}:{start_index + _size}"
        )

        logger.info(f"Starting fetching data for {len(epd_ids)} EPDs")
        [
            await fetching.get_and_save_epd(
                url=data.get("uri"),
                data={"source": "ECOPlatform", **data},
                base_url=data.get("uri").split("/processes")[0],
            )
            for data in epd_ids
        ]
        start_index += data_size

    logger.info("Done processing data")

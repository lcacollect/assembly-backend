import asyncio
import json
import logging
from datetime import date

import httpx
from httpx import HTTPStatusError
from lcaconfig.connection import create_postgres_engine
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from exceptions.import_data import EPDParseError
from models.assembly import Assembly
from models.epd import EPD

logger = logging.getLogger(__name__)


UNIT_NAME_MAP = {
    "Volume": "m3",
    "Mass": "kg",
    "Area": "m2",
    "Number of pieces": "pcs",
    "Length": "m",
    "Volumen": "m3",
    "Fläche": "m2",
    "Gewicht": "kg",
    "Quadratmeter": "m2",
    "Stück": "pcs",
}


def get_version(data: dict, additional_data):
    if additional_data.get("version"):
        return additional_data.get("version")
    try:
        return data["administrativeInformation"]["publicationAndOwnership"]["dataSetVersion"]
    except TypeError:
        return None


def get_location(data: dict, additional_data: dict) -> str:
    if additional_data.get("location"):
        return additional_data.get("location")

    return data.get("locationOfOperationSupplyOrProduction", {}).get("location", "Unknown")


def get_owner(data: dict, additional_data: dict) -> str:
    if additional_data.get("owner"):
        return additional_data.get("owner")

    ownership = data.get("publicationAndOwnership", {}).get("referenceToOwnershipOfDataSet")

    owner = None
    for elem in ownership.get("shortDescription"):
        if elem.get("lang") == "en":
            return elem.get("value")
        else:
            owner = elem.get("value")

    return owner


def get_lifetime(data: dict[str, dict]) -> int:
    lifetime: int = data.get("dataEntryBy").get("timeStamp")
    return lifetime


def parse_epd_data(epd_data: dict, additional_data: dict) -> EPD | None:
    version = get_version(epd_data, additional_data)

    gwp, odp, ap, ep, pocp = get_impact_categories(epd_data)
    pere, penre = get_energy_indicators(epd_data)
    flow_data = parse_flow_data(additional_data.get("flow", {}))

    return EPD(
        gwp_by_phases=gwp,
        odp_by_phases=odp,
        ap_by_phases=ap,
        ep_by_phases=ep,
        pocp_by_phases=pocp,
        penre_by_phases=penre,
        pere_by_phases=pere,
        source=additional_data.get("source"),
        version=version,
        type=additional_data.get("type"),
        owner=get_owner(epd_data["administrativeInformation"], additional_data),
        region=get_location(epd_data["processInformation"]["geography"], additional_data),
        source_data=additional_data.get("source_data", ""),
        unit=flow_data.get("unit"),
        meta_fields=flow_data.get("conversions", {}),
        **get_dataset_information(
            epd_data["processInformation"]["dataSetInformation"],
            additional_data,
        ),
        **get_time_information(epd_data["processInformation"]["time"]),
    )


def get_impact_categories(epd_data: dict):
    result = epd_data["LCIAResults"]["LCIAResult"]
    gwp, odp, ap, ep, pocp = {}, {}, {}, {}, {}
    for elem in result:
        descriptions: list[dict[str, str]]
        descriptions = elem.get("referenceToLCIAMethodDataSet", {}).get("shortDescription", [])
        for description in descriptions:
            lang = description.get("lang", " ")
            descr_value = description.get("value", " ")
            if lang != "en":
                continue
            if descr_value.startswith("Global"):
                gwp = get_indicator_by_phase(elem)
            elif descr_value.startswith("Ozone"):
                odp = get_indicator_by_phase(elem)
            elif descr_value.startswith("Acidification"):
                ap = get_indicator_by_phase(elem)
            elif descr_value.startswith("Eutrophication"):
                ep = get_indicator_by_phase(elem)
            elif descr_value.startswith("Photochemical"):
                pocp = get_indicator_by_phase(elem)

    return gwp, odp, ap, ep, pocp


def get_energy_indicators(epd_data: dict):
    pere = {}
    penre = {}

    for elem in epd_data.get("exchanges", {}).get("exchange", []):
        descriptions = elem.get("referenceToLCIAMethodDataSet", {}).get("shortDescription", [])
        for description in descriptions:
            lang = description.get("lang", " ")
            descr_value = description.get("value", " ")
            if lang != "en":
                continue
            if "PERE" in descr_value:
                pere = get_indicator_by_phase(elem)
            elif "PENRE" in descr_value:
                penre = get_indicator_by_phase(elem)

    return pere, penre


def get_indicator_by_phase(data: dict) -> dict:
    indicator = data.get("other", {}).get("anies")

    indicator_by_phase = {}
    for phase in indicator:
        if phase.get("module"):
            try:
                indicator_by_phase[phase.get("module")] = float(phase.get("value"))
            except (ValueError, TypeError):
                continue

    return indicator_by_phase


async def get_epd_data(url: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{url}{'&' if '?' in url else '?'}format=json", follow_redirects=True)
        response.raise_for_status()

        data = response.json()

    return data


def get_epd_name(_data: dict, additional_data: dict) -> str:
    if additional_data.get("name"):
        return additional_data.get("name")

    data = _data["name"]["baseName"]
    name_other = None

    for _name in data:
        if _name.get("lang") == "en":
            return _name.get("value")
        else:
            name_other = _name.get("value")

    if not name_other:
        raise EPDParseError(f"Could not find name for EPD with name data: {json.dumps(_data)}")

    return name_other


def get_dataset_category(data: dict) -> str:
    return (
        data.get("classificationInformation", {})
        .get("classification", [{}])[0]
        .get("class", [{}])[0]
        .get("value", "Unknown")
    )


def get_dataset_information(data: dict, additional_data: dict) -> dict:
    name = get_epd_name(data, additional_data)
    uid = data["UUID"]
    category = get_dataset_category(data)

    return {"name": name, "origin_id": uid, "category": category}


def get_time_information(data: dict) -> dict:
    expiration_date = data["dataSetValidUntil"]
    date_updated = data["referenceYear"]

    return {
        "expiration_date": date(year=expiration_date, month=1, day=1),
        "date_updated": date(year=date_updated, month=1, day=1),
    }


def parse_flow_data(data: dict) -> dict:
    flow_data = {"unit": None}
    flow_properties = data.get("flowProperties", {}).get("flowProperty", [])
    dataset_information = (
        data.get("flowInformation", {}).get("dataSetInformation", {}).get("other", {}).get("anies", {})
    )

    flow_data.update({"unit": get_functional_unit(flow_properties)})
    flow_data.update({"conversions": get_functional_unit_conversions(dataset_information)})

    return flow_data


def get_functional_unit(flow_properties: dict) -> str:
    for flow_property in flow_properties:
        if flow_property.get("meanValue", 0) == 1:
            unit = None
            for description in flow_property.get("referenceToFlowPropertyDataSet", {}).get("shortDescription", []):
                if description.get("lang") == "en":
                    return UNIT_NAME_MAP.get(description.get("value"), description.get("value"))
                else:
                    unit = description.get("value")

            return UNIT_NAME_MAP.get(unit, unit)


def get_functional_unit_conversions(dataset_information: dict) -> dict:
    conversions = {}

    for information in dataset_information:
        for material in information.get("Material", []):
            for property_data in material.get("BulkDetails", {}).get("PropertyData", {}):
                format = property_data.get("Data", {}).get("format")
                value = property_data.get("Data", {}).get("value")
                value = float(value) if format == "float" else value
                if _property := property_data.get("property"):
                    for detail in information.get("Metadata", {}).get("PropertyDetails"):
                        if detail.get("id") == _property:
                            conversions.update({detail.get("Units", {}).get("name"): value})

    return conversions


async def get_flow_dataset(epd_data, base_url) -> dict:
    uid, version = None, None
    for exchange in epd_data.get("exchanges", {}).get("exchange", []):
        if not exchange.get("other"):
            uid = exchange.get("referenceToFlowDataSet", {}).get("refObjectId")
            version = exchange.get("referenceToFlowDataSet", {}).get("version")
            break

    if not uid:
        return {}
    try:
        return await get_epd_data(f"{base_url}/flows/{uid}{f'?version={version}' if version else ''}")
    except HTTPStatusError:
        return {}


async def get_and_save_epd(url: str, data: dict, base_url: str):
    logger.info(f"Fetching {url}")
    epd_data = await get_epd_data(url)
    if not epd_data:
        return

    data.update(
        {
            "flow": await get_flow_dataset(epd_data, base_url),
            "source_data": f"{url}&format=html",
        }
    )
    epd = parse_epd_data(epd_data, data)

    if not epd:
        logger.info(f"No EPD object created for {url}. Doesn't save to local database")
    else:
        logger.info(f"Saving {epd.id} to database - {epd}")
        async with AsyncSession(create_postgres_engine()) as session:
            _epd = (
                await session.exec(select(EPD).where(EPD.origin_id == epd.origin_id, EPD.version == epd.version))
            ).first()
            if not _epd:
                session.add(epd)
                await session.commit()
            else:
                logger.info(
                    f"EPD with origin_id: {epd.origin_id} and version: {epd.version} already exists. "
                    f"Updating EPD in database."
                )
                await update_epd(_epd, epd, session)


async def update_epd(original_epd, new_epd, session):
    fields = [
        "category",
        "expiration_date",
        "gwp_by_phases",
        "name",
        "owner",
        "region",
        "source",
        "type",
    ]
    for field in fields:
        if getattr(original_epd, field) != getattr(new_epd, field):
            setattr(original_epd, field, getattr(new_epd, field))

    session.add(original_epd)
    await session.commit()

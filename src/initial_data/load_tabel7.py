import asyncio

from datetime import date

import io
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from pathlib import Path
import csv

from lcacollect_config.connection import create_postgres_engine
from models.epd import EPD


async def load(path: Path):
    reader = csv.DictReader(io.StringIO(path.read_text()))

    async with AsyncSession(create_postgres_engine()) as session:
        for row in reader:
            if row.get("Sorterings ID").startswith("#S"):
                continue

            _epd = (await session.exec(select(EPD).where(EPD.comment == row.get("Sorterings ID")))).first()
            if _epd:
                continue

            epd = EPD(
                name=row.get("Navn DK"),
                version="version 2 - 201222",
                declared_unit=convert_unit(row.get("Deklareret enhed (FU)")),
                valid_until=date(year=2025, month=12, day=22),
                published_date=date(year=2020, month=12, day=22),
                source=row.get("Url (link)"),
                subtype=convert_subtype(row.get("Data type")),
                comment=row.get("Sorterings ID"),
                reference_service_life=None,
                location="DK",
                conversions=[
                    {"to": "KG",
                    "value": float(row.get("Masse faktor"))*float(row.get("Deklareret faktor (FU)"))}
                ],
                gwp={
                    "a1a3": convert_gwp(row.get("Global Opvarmning, modul A1-A3"), float(row.get("Deklareret faktor (FU)"))),
                    "a4": None,
                    "a5": None,
                    "b1": None,
                    "b2": None,
                    "b3": None,
                    "b4": None,
                    "b5": None,
                    "b6": None,
                    "b7": None,
                    "c1": None,
                    "c2": None,
                    "c3": convert_gwp(row.get("Global Opvarmning, modul C3"), float(row.get("Deklareret faktor (FU)"))),
                    "c4": convert_gwp(row.get("Global Opvarmning, modul C4"), float(row.get("Deklareret faktor (FU)"))),
                    "d": convert_gwp(row.get("Global Opvarmning, modul D"), float(row.get("Deklareret faktor (FU)"))),
                },
                odp={},
                ap={},
                ep={},
                pocp={},
                penre={},
                pere={},
                meta_fields={},
            )
            session.add(epd)
            await session.commit()

def convert_unit(unit: str) -> str:
    if unit == "STK":
        return "pcs"
    else:
        return unit.lower()


def convert_subtype(subtype: str) -> str:
    map = {
        "Generisk data": "Generic",
        "Branche data": "Industry",
    }
    return map.get(subtype)

def convert_gwp(gwp: str, declared_factor: float) -> float | None:
    if gwp == "-":
        return None
    else:
        return float(gwp) / declared_factor


if __name__ == "__main__":
    p = Path(__file__).parent / "BR18_bilag_2_tabel_7_version_2_201222.csv"
    asyncio.run(load(p))

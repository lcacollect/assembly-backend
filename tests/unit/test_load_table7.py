from initial_data.load_tabel7 import load
import pytest
from pathlib import Path


@pytest.mark.asyncio
async def test_load_table7(db):
    file = Path(__file__).parent.parent.parent / "src" / "initial_data" / "BR18_bilag_2_tabel_7_version_2_201222.csv"
    await load(file)
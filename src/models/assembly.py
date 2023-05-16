from enum import Enum
from typing import List, Optional

from lcaconfig.formatting import string_uuid
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSON
from sqlmodel import Field, Relationship, SQLModel


class AssemblyUnit(str, Enum):
    m = "M"
    m2 = "M2"
    m3 = "M3"
    kg = "KG"
    pcs = "Pcs"


class Assembly(SQLModel, table=True):
    """Assembly database class"""

    id: Optional[str] = Field(default_factory=string_uuid, primary_key=True)
    name: str = Field(index=True)
    category: str
    life_time: float = 50
    meta_fields: dict = Field(default=dict, sa_column=Column(JSON), nullable=False)
    unit: str = "M2"
    conversion_factor: float = 1.0
    project_id: str | None
    description: str | None

    layers: List["AssemblyEPDLink"] = Relationship(back_populates="assembly")

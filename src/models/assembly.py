from enum import Enum
from typing import TYPE_CHECKING, Optional

from lcacollect_config.formatting import string_uuid
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSON
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from models.links import ProjectAssemblyEPDLink


class AssemblyUnit(str, Enum):
    m = "M"
    m2 = "M2"
    m3 = "M3"
    kg = "KG"
    pcs = "Pcs"


class ProjectAssembly(SQLModel, table=True):
    """Assembly database class"""

    id: Optional[str] = Field(
        default_factory=string_uuid,
        primary_key=True,
        nullable=False,
        sa_column_kwargs={"unique": True},
    )
    name: str = Field(index=True)
    category: str
    life_time: float = 50.0
    meta_fields: dict = Field(default=dict, sa_column=Column(JSON), nullable=False)
    unit: str = "M2"
    conversion_factor: float = 1.0
    project_id: str
    description: str | None

    layers: list["ProjectAssemblyEPDLink"] = Relationship(
        back_populates="assembly", sa_relationship_kwargs={"cascade": "all,delete"}
    )

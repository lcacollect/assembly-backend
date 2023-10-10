from enum import Enum
from typing import TYPE_CHECKING, Optional

from lcacollect_config.formatting import string_uuid
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSON
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from models.links import AssemblyEPDLink, ProjectAssemblyEPDLink


class AssemblyUnit(str, Enum):
    m = "M"
    m2 = "M2"
    m3 = "M3"
    kg = "KG"
    pcs = "Pcs"


class AssemblyBase(SQLModel):
    name: str = Field(index=True)
    category: str
    life_time: float = 50.0
    unit: str = "M2"
    conversion_factor: float = 1.0
    description: str | None

    meta_fields: dict = Field(default=dict, sa_column=Column(JSON), nullable=False)


class Assembly(AssemblyBase, table=True):
    id: Optional[str] = Field(default_factory=string_uuid, primary_key=True)
    source: str

    # Relationships
    project_assemblies: list["ProjectAssembly"] = Relationship(back_populates="origin")
    layers: list["AssemblyEPDLink"] = Relationship(
        back_populates="assembly", sa_relationship_kwargs={"cascade": "all,delete"}
    )


class ProjectAssembly(AssemblyBase, table=True):
    """Assembly database class"""

    id: Optional[str] = Field(
        default_factory=string_uuid,
        primary_key=True,
        nullable=False,
        sa_column_kwargs={"unique": True},
    )
    project_id: str

    origin_id: str | None = Field(foreign_key="assembly.id", nullable=True)
    origin: Assembly | None = Relationship(back_populates="project_assemblies")
    layers: list["ProjectAssemblyEPDLink"] = Relationship(
        back_populates="assembly", sa_relationship_kwargs={"cascade": "all,delete"}
    )

    @classmethod
    def create_from_assembly(cls, assembly: Assembly, project_id: str):
        org_data = assembly.dict(exclude={"id", "origin_id", "layers", "source"})
        project_assembly = cls(**org_data, project_id=project_id, origin=assembly, origin_id=assembly.id)

        return project_assembly

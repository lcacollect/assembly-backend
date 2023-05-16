from datetime import date
from typing import List, Optional

from lcaconfig.formatting import string_uuid
from sqlalchemy import Column, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSON
from sqlmodel import Field, Relationship, SQLModel

from models.links import AssemblyEPDLink


class EPDBase(SQLModel):
    name: str = Field(index=True)
    category: str
    gwp_by_phases: dict = Field(default=dict, sa_column=Column(JSON), nullable=False)
    odp_by_phases: dict = Field(default=dict, sa_column=Column(JSON), nullable=False)
    ap_by_phases: dict = Field(default=dict, sa_column=Column(JSON), nullable=False)
    ep_by_phases: dict = Field(default=dict, sa_column=Column(JSON), nullable=False)
    pocp_by_phases: dict = Field(default=dict, sa_column=Column(JSON), nullable=False)
    penre_by_phases: dict = Field(default=dict, sa_column=Column(JSON), nullable=False)
    pere_by_phases: dict = Field(default=dict, sa_column=Column(JSON), nullable=False)
    version: str
    unit: str | None
    expiration_date: date
    date_updated: date
    source: str
    owner: str
    region: str
    type: str
    meta_fields: dict = Field(default=dict, sa_column=Column(JSON), nullable=False)
    source_data: str | None

    def __repr__(self):
        return f"{self.name} - {self.version} - {self.source}"

    def __str__(self):
        return self.__repr__()


class EPD(EPDBase, table=True):
    """
    EPD database class
    The origin_id is the id from the data source fx. Ökobau or ECOplatform
    """

    __table_args__ = (UniqueConstraint("origin_id", "version", name="origin_version"),)

    id: Optional[str] = Field(default_factory=string_uuid, primary_key=True)
    origin_id: Optional[str] = None

    # Relationships
    project_epds: list["ProjectEPD"] = Relationship(back_populates="origin")


class ProjectEPD(EPDBase, table=True):
    """Project related EPD class"""

    id: Optional[str] = Field(default_factory=string_uuid, primary_key=True)
    project_id: str
    kg_per_m3: float | None
    kg_per_m2: float | None
    thickness: float | None

    # Relationships
    origin_id: str = Field(foreign_key="epd.id")
    origin: EPD = Relationship(back_populates="project_epds")
    assembly_links: List[AssemblyEPDLink] = Relationship(back_populates="epd")

    @classmethod
    def create_from_epd(cls, epd: EPD, project_id: str):
        org_data = epd.dict()
        del org_data["id"]
        return cls(**org_data, project_id=project_id, origin=epd)

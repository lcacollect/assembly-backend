from datetime import date
from typing import TYPE_CHECKING, Optional

from lcacollect_config.formatting import string_uuid
from sqlalchemy import Column, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import RelationshipProperty
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from models.links import AssemblyEPDLink, ProjectAssemblyEPDLink


class EPDBase(SQLModel):
    name: str = Field(index=True)
    version: str
    declared_unit: str | None
    valid_until: date
    published_date: date
    source: str
    location: str
    subtype: str
    comment: str | None
    is_transport: bool = False
    reference_service_life: int | None
    conversions: list = Field(default=list, sa_column=Column(JSON), nullable=False)

    gwp: dict = Field(default=dict, sa_column=Column(JSON), nullable=False)
    odp: dict = Field(default=dict, sa_column=Column(JSON), nullable=False)
    ap: dict = Field(default=dict, sa_column=Column(JSON), nullable=False)
    ep: dict = Field(default=dict, sa_column=Column(JSON), nullable=False)
    pocp: dict = Field(default=dict, sa_column=Column(JSON), nullable=False)
    penre: dict = Field(default=dict, sa_column=Column(JSON), nullable=False)
    pere: dict = Field(default=dict, sa_column=Column(JSON), nullable=False)

    meta_fields: dict = Field(default=dict, sa_column=Column(JSON), nullable=False)

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
    assembly_links: list["AssemblyEPDLink"] = Relationship(
        back_populates="epd",
        sa_relationship=RelationshipProperty(
            "AssemblyEPDLink",
            primaryjoin="foreign(EPD.id) == AssemblyEPDLink.epd_id",
            uselist=True,
        ),
    )
    transport_links: list["AssemblyEPDLink"] = Relationship(
        back_populates="transport_epd",
        sa_relationship=RelationshipProperty(
            "AssemblyEPDLink",
            primaryjoin="foreign(EPD.id) == AssemblyEPDLink.transport_epd_id",
            uselist=True,
        ),
    )


class ProjectEPD(EPDBase, table=True):
    """Project related EPD class"""

    id: Optional[str] = Field(default_factory=string_uuid, primary_key=True)
    project_id: str

    # Relationships
    origin_id: str = Field(foreign_key="epd.id")
    origin: EPD = Relationship(back_populates="project_epds")
    assembly_links: list["ProjectAssemblyEPDLink"] = Relationship(
        back_populates="epd",
        sa_relationship=RelationshipProperty(
            "ProjectAssemblyEPDLink",
            primaryjoin="foreign(ProjectEPD.id) == ProjectAssemblyEPDLink.epd_id",
            uselist=True,
        ),
    )
    transport_links: list["AssemblyEPDLink"] = Relationship(
        back_populates="transport_epd",
        sa_relationship=RelationshipProperty(
            "ProjectAssemblyEPDLink",
            primaryjoin="foreign(ProjectEPD.id) == ProjectAssemblyEPDLink.transport_epd_id",
            uselist=True,
        ),
    )

    @classmethod
    def create_from_epd(cls, epd: EPD, project_id: str):
        org_data = epd.dict(exclude={"id", "origin_id"})
        return cls(**org_data, project_id=project_id, origin=epd, origin_id=epd.id)

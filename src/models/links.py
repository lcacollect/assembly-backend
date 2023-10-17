from typing import TYPE_CHECKING, Optional

from lcacollect_config.formatting import string_uuid
from sqlalchemy.orm import RelationshipProperty
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from models.assembly import Assembly, ProjectAssembly
    from models.epd import EPD, ProjectEPD


class AssemblyEPDLinkBase(SQLModel):
    """Assembly EPD Database base class"""

    conversion_factor: float = 1.0
    reference_service_life: Optional[int] = None
    description: str = ""
    name: str = ""

    transport_distance: float = 0.0
    transport_conversion_factor: float = 1.0


class AssemblyEPDLink(AssemblyEPDLinkBase, table=True):
    """Assembly EPD Database class"""

    id: Optional[str] = Field(default_factory=string_uuid, primary_key=True)
    assembly_id: Optional[str] = Field(default=None, foreign_key="assembly.id", primary_key=True)
    epd_id: Optional[str] = Field(default=None, foreign_key="epd.id", primary_key=True)
    transport_epd_id: Optional[str] = Field(default=None, foreign_key="epd.id")

    assembly: "Assembly" = Relationship(back_populates="layers")
    epd: "EPD" = Relationship(
        back_populates="assembly_links",
        sa_relationship=RelationshipProperty(
            "EPD",
            primaryjoin="foreign(AssemblyEPDLink.epd_id) == EPD.id",
            uselist=False,
        ),
    )
    transport_epd: "EPD" = Relationship(
        back_populates="transport_links",
        sa_relationship=RelationshipProperty(
            "EPD",
            primaryjoin="foreign(AssemblyEPDLink.transport_epd_id) == EPD.id",
            uselist=False,
        ),
    )


class ProjectAssemblyEPDLink(AssemblyEPDLinkBase, table=True):
    """Project Assembly EPD Database class"""

    id: Optional[str] = Field(default_factory=string_uuid, primary_key=True)
    assembly_id: Optional[str] = Field(default=None, foreign_key="projectassembly.id", primary_key=True)
    epd_id: Optional[str] = Field(default=None, foreign_key="projectepd.id", primary_key=True)
    transport_epd_id: Optional[str] = Field(default=None, foreign_key="projectepd.id")

    assembly: "ProjectAssembly" = Relationship(back_populates="layers")
    epd: "ProjectEPD" = Relationship(
        back_populates="assembly_links",
        sa_relationship=RelationshipProperty(
            "ProjectEPD",
            primaryjoin="foreign(ProjectAssemblyEPDLink.epd_id) == ProjectEPD.id",
            uselist=False,
        ),
    )
    transport_epd: "ProjectEPD" = Relationship(
        back_populates="transport_links",
        sa_relationship=RelationshipProperty(
            "ProjectEPD",
            primaryjoin="foreign(ProjectAssemblyEPDLink.transport_epd_id) == ProjectEPD.id",
            uselist=False,
        ),
    )

    @classmethod
    def create_from_link(cls, link: AssemblyEPDLink):
        org_data = link.dict(exclude={"id", "assembly_id", "epd_id", "transport_epd_id"})
        return cls(**org_data)

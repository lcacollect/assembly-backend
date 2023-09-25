from typing import TYPE_CHECKING, Optional

from lcacollect_config.formatting import string_uuid
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
    transport_type: Optional[str] = None
    transport_distance: Optional[float] = None
    transport_unit: Optional[str] = None


class AssemblyEPDLink(AssemblyEPDLinkBase, table=True):
    """Assembly EPD Database class"""

    id: Optional[str] = Field(default_factory=string_uuid, primary_key=True)
    assembly_id: Optional[str] = Field(default=None, foreign_key="assembly.id", primary_key=True)
    epd_id: Optional[str] = Field(default=None, foreign_key="epd.id", primary_key=True)

    assembly: "Assembly" = Relationship(back_populates="layers")
    epd: "EPD" = Relationship(back_populates="assembly_links")


class ProjectAssemblyEPDLink(AssemblyEPDLinkBase, table=True):
    """Project Assembly EPD Database class"""

    id: Optional[str] = Field(default_factory=string_uuid, primary_key=True)
    assembly_id: Optional[str] = Field(default=None, foreign_key="projectassembly.id", primary_key=True)
    epd_id: Optional[str] = Field(default=None, foreign_key="projectepd.id", primary_key=True)

    assembly: "ProjectAssembly" = Relationship(back_populates="layers")
    epd: "ProjectEPD" = Relationship(back_populates="assembly_links")

    @classmethod
    def create_from_link(cls, link: AssemblyEPDLink):
        org_data = link.dict(exclude={"id", "assembly_id", "epd_id"})
        return cls(**org_data)

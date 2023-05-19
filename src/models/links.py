from typing import TYPE_CHECKING, Optional

from lcacollect_config.formatting import string_uuid
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from models.assembly import Assembly
    from models.epd import ProjectEPD


class AssemblyEPDLink(SQLModel, table=True):
    """Assembly EPD Database class"""

    id: Optional[str] = Field(default_factory=string_uuid, primary_key=True)
    assembly_id: Optional[str] = Field(default=None, foreign_key="assembly.id", primary_key=True)
    epd_id: Optional[str] = Field(default=None, foreign_key="projectepd.id", primary_key=True)
    conversion_factor: float = 1.0
    name: str = ""
    assembly: "Assembly" = Relationship(back_populates="layers")
    epd: "ProjectEPD" = Relationship(back_populates="assembly_links")

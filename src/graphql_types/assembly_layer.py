from enum import Enum
from typing import Annotated

import strawberry
from strawberry import UNSET


@strawberry.enum
class TransportType(Enum):
    truck = "truck"
    train = "train"
    ship = "ship"
    plane = "plane"


@strawberry.type
class GraphQLAssemblyLayer:
    id: str | None
    epd: Annotated["GraphQLProjectEPD", strawberry.lazy("schema.epd")]

    @strawberry.field
    def epd_id(self) -> str:
        return self.epd.id

    name: str | None
    conversion_factor: float | None
    reference_service_life: int | None
    description: str | None

    transport_type: TransportType | None
    transport_distance: float | None
    transport_unit: str | None


@strawberry.input
class AssemblyLayerInput:
    epd_id: str
    id: str | None = UNSET
    name: str | None = UNSET
    conversion_factor: float | None = UNSET
    reference_service_life: int | None = UNSET
    description: str | None = UNSET

    transport_type: TransportType | None = UNSET
    transport_distance: float | None = UNSET
    transport_unit: str | None = UNSET


@strawberry.input
class AssemblyLayerUpdateInput:
    epd_id: str
    id: str
    name: str | None = UNSET
    conversion_factor: float | None = UNSET
    reference_service_life: int | None = UNSET
    description: str | None = UNSET

    transport_type: TransportType | None = UNSET
    transport_distance: float | None = UNSET
    transport_unit: str | None = UNSET

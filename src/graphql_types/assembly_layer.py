from typing import TYPE_CHECKING, Annotated

import strawberry

if TYPE_CHECKING:  # pragma: no cover
    from schema.epd import GraphQLProjectEPD


@strawberry.type
class GraphQLAssemblyLayer:
    id: str | None
    epd: Annotated["GraphQLProjectEPD", strawberry.lazy("schema.epd")]
    epd_id: str

    name: str | None
    conversion_factor: float | None
    reference_service_life: int | None
    description: str | None

    transport_epd: Annotated["GraphQLProjectEPD", strawberry.lazy("schema.epd")] | None
    transport_distance: float | None
    transport_conversion_factor: float


@strawberry.input
class AssemblyLayerInput:
    epd_id: str
    id: str | None = None
    name: str | None = None
    conversion_factor: float | None = None
    reference_service_life: int | None = None
    description: str | None = None

    transport_epd_id: str | None = None
    transport_distance: float | None = None
    transport_conversion_factor: float | None = 1.0


@strawberry.input
class AssemblyLayerUpdateInput:
    epd_id: str
    id: str
    name: str | None = None
    conversion_factor: float | None = None
    reference_service_life: int | None = None
    description: str | None = None

    transport_epd_id: str | None = None
    transport_distance: float | None = None
    transport_conversion_factor: float | None = None

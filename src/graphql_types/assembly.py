from enum import Enum
import strawberry
from strawberry.scalars import JSON
from .assembly_layer import GraphQLAssemblyLayer


@strawberry.enum
class GraphQLAssemblyUnit(Enum):
    m = "M"
    m2 = "M2"
    m3 = "M3"
    kg = "KG"
    pcs = "Pcs"


@strawberry.type
class GraphQLProjectAssembly:
    id: str
    name: str
    project_id: str
    category: str
    life_time: float
    meta_fields: JSON | None
    unit: GraphQLAssemblyUnit
    conversion_factor: float
    description: str | None

    layers: list[GraphQLAssemblyLayer]

    @strawberry.field
    def gwp(self, phases: list[str] | None = None) -> float:
        """Calculate the gwp of the assembly based on the underlying layers."""

        if self.layers:
            return sum([calculate_indicator(layer.epd.gwp, phases) * layer.conversion_factor for layer in self.layers])
        return 0


@strawberry.input
class ProjectAssemblyUpdateInput:
    id: str
    name: str | None = None
    category: str | None = None
    description: str | None = None
    life_time: float | None = None
    meta_fields: JSON | None = None
    conversion_factor: float | None = None
    unit: GraphQLAssemblyUnit | None = None


@strawberry.input
class ProjectAssemblyAddInput:
    name: str
    category: str
    project_id: str
    description: str | None = None
    life_time: float | None = 50.0
    meta_fields: JSON | None = None
    conversion_factor: float | None = 1.0
    unit: GraphQLAssemblyUnit


def calculate_indicator(data_by_phases: dict, phases: list[str] | None) -> float:
    if phases:
        return sum([data_by_phases.get(phase, 0) for phase in phases])
    else:
        return data_by_phases.get("a1a3", 0) or 0
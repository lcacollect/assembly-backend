from enum import Enum

import strawberry
from pydantic import BaseModel
from strawberry.scalars import JSON

from .assembly_layer import GraphQLAssemblyLayer


@strawberry.enum
class GraphQLAssemblyUnit(Enum):
    m = "M"
    m2 = "M2"
    m3 = "M3"
    kg = "KG"
    pcs = "Pcs"


class BaseAssembly(BaseModel):
    id: str
    name: str
    category: str
    life_time: float
    conversion_factor: float
    description: str | None


def calculate_impact_category(impact_category: str, layers, phases: list[str] | None = None) -> float:
    """Calculate the impact category of the assembly based on the underlying layers."""

    return sum(
        [calculate_indicator(getattr(layer.epd, impact_category), phases) * layer.conversion_factor for layer in layers]
    )


@strawberry.type
class GraphQLAssembly:
    id: str
    name: str
    category: str
    life_time: float
    conversion_factor: float
    description: str | None
    meta_fields: JSON | None
    unit: GraphQLAssemblyUnit

    layers: list[GraphQLAssemblyLayer | None]

    @strawberry.field
    def gwp(self, phases: list[str] | None = None) -> float:
        """Calculate the gwp of the assembly based on the underlying layers."""

        if self.layers:
            return calculate_impact_category("gwp", self.layers, phases)
        return 0


@strawberry.type
class GraphQLProjectAssembly:
    id: str
    name: str
    category: str
    life_time: float
    conversion_factor: float
    description: str | None
    project_id: str
    meta_fields: JSON | None
    unit: GraphQLAssemblyUnit

    layers: list[GraphQLAssemblyLayer]

    @strawberry.field
    def gwp(self, phases: list[str] | None = None) -> float:
        """Calculate the gwp of the assembly based on the underlying layers."""

        if self.layers:
            return calculate_impact_category("gwp", self.layers, phases)
        return 0


class BaseAssemblyUpdateInput(BaseModel):
    id: str
    name: str | None = None
    category: str | None = None
    description: str | None = None
    life_time: float | None = None
    conversion_factor: float | None = None


@strawberry.experimental.pydantic.input(model=BaseAssemblyUpdateInput, all_fields=True)
class ProjectAssemblyUpdateInput:
    meta_fields: JSON | None = None
    unit: GraphQLAssemblyUnit | None = None


@strawberry.experimental.pydantic.input(model=BaseAssemblyUpdateInput, all_fields=True)
class AssemblyUpdateInput:
    meta_fields: JSON | None = None
    unit: GraphQLAssemblyUnit | None = None


class BaseAssemblyAddInput(BaseModel):
    name: str
    category: str
    description: str | None = None
    life_time: float | None = 50.0
    conversion_factor: float | None = 1.0


@strawberry.experimental.pydantic.input(model=BaseAssemblyAddInput, all_fields=True)
class ProjectAssemblyAddInput:
    project_id: str
    meta_fields: JSON | None = None
    unit: GraphQLAssemblyUnit


@strawberry.experimental.pydantic.input(model=BaseAssemblyAddInput, all_fields=True)
class AssemblyAddInput:
    meta_fields: JSON | None = None
    unit: GraphQLAssemblyUnit


def calculate_indicator(data_by_phases: dict, phases: list[str] | None) -> float:
    if phases:
        return sum([data_by_phases.get(phase, 0) for phase in phases])
    else:
        return data_by_phases.get("a1a3", 0) or 0

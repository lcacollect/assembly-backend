from typing import Optional

import strawberry
from lcacollect_config.graphql.input_filters import (
    BaseFilter,
    FilterOptions,
    SortOptions,
)


@strawberry.input
class EPDFilters(BaseFilter):
    id: Optional[FilterOptions] = None
    unit: Optional[FilterOptions] = None
    name: Optional[FilterOptions] = None
    category: Optional[FilterOptions] = None
    source: Optional[FilterOptions] = None
    type: Optional[FilterOptions] = None
    region: Optional[FilterOptions] = None
    owner: Optional[FilterOptions] = None
    is_transport: Optional[FilterOptions] = None


@strawberry.input
class EPDSort(BaseFilter):
    name: Optional[SortOptions] = None
    unit: Optional[SortOptions] = None
    category: Optional[SortOptions] = None
    source: Optional[SortOptions] = None
    type: Optional[SortOptions] = None
    region: Optional[SortOptions] = None
    owner: Optional[SortOptions] = None
    is_transport: Optional[SortOptions] = None


@strawberry.input
class ProjectEPDFilters(BaseFilter):
    id: Optional[FilterOptions] = None
    name: Optional[FilterOptions] = None
    unit: Optional[SortOptions] = None
    category: Optional[FilterOptions] = None
    project_id: Optional[FilterOptions] = None
    source: Optional[FilterOptions] = None
    type: Optional[FilterOptions] = None
    region: Optional[FilterOptions] = None
    owner: Optional[FilterOptions] = None
    is_transport: Optional[FilterOptions] = None


@strawberry.input
class AssemblyFilters(BaseFilter):
    id: Optional[FilterOptions] = None
    name: Optional[FilterOptions] = None
    category: Optional[FilterOptions] = None
    life_time: Optional[FilterOptions] = None
    description: Optional[FilterOptions] = None
    source: Optional[FilterOptions] = None

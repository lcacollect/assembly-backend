import base64
import logging
from datetime import date
from typing import Optional

import strawberry
from lcacollect_config.exceptions import DatabaseItemNotFound
from lcacollect_config.graphql.input_filters import (filter_model_query,
                                             sort_model_query)
from lcacollect_config.graphql.pagination import Connection, Cursor, Edge, PageInfo
from sqlalchemy import func
from sqlmodel import select
from strawberry import UNSET
from strawberry.scalars import JSON
from strawberry.types import Info

import models.epd as models_epd
import schema.assembly as schema_assembly
from schema.directives import Keys
from schema.inputs import EPDFilters, EPDSort, ProjectEPDFilters

logger = logging.getLogger(__name__)


async def epds_query(
    info: Info,
    filters: Optional[EPDFilters] = None,
    sort_by: Optional[EPDSort] = None,
    count: int = 50,
    after: Optional[Cursor] = UNSET,
) -> Connection["GraphQLEPD"]:
    """
    Query the database for EPD entries.
    This query is paginated.
    The pagination inspiration source is from Strawberry's docs: https://strawberry.rocks/docs/guides/pagination
    """

    session = info.context.get("session")

    # Build EPD query
    query = select(models_epd.EPD)
    if filters:
        query = filter_model_query(models_epd.EPD, filters, query=query)

    # Get the total number of epds in query
    total_count = (await session.exec(select(func.count()).select_from(query.subquery()))).one()

    # limit the query for pagination
    after = after if after is not UNSET else None
    if after:
        query = query.where(models_epd.EPD.id > after)
    query = query.limit(count + 1)
    if sort_by:
        query = sort_model_query(models_epd.EPD, sort_by, query=query)
    else:
        query = query.order_by(models_epd.EPD.id)

    epds = (await session.exec(query)).all()
    edges = [Edge(node=epd, cursor=epd.id) for epd in epds]

    # Get the end cursor
    end_cursor = None
    if len(edges) > count:
        end_cursor = edges[-1].cursor
    elif len(edges) > 1:
        end_cursor = edges[-2].cursor

    return Connection(
        page_info=PageInfo(
            has_previous_page=False,
            has_next_page=total_count > count,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=end_cursor,
        ),
        edges=edges[:-1]
        if len(edges) > count
        else edges,  # exclude last one as it was fetched to know if there is a next page
        num_edges=total_count,
    )


def build_epd_cursor(epd: models_epd.EPD):
    return base64.b64encode(epd.id.encode()).decode()


async def project_epds_query(
    info: Info, project_id: str, filters: Optional[ProjectEPDFilters] = None
) -> list["GraphQLProjectEPD"]:
    session = info.context.get("session")
    query = select(models_epd.ProjectEPD).where(models_epd.ProjectEPD.project_id == project_id)
    if not filters:
        epds = await session.exec(query)
        return epds.all()
    else:
        query = filter_model_query(models_epd.ProjectEPD, filters, query=query)
        epds = await session.exec(query)
        return epds.all()


async def add_project_epd_mutation(info: Info, project_id: str, origin_id: str) -> "GraphQLProjectEPD":
    session = info.context.get("session")

    epd = await session.get(models_epd.EPD, origin_id)
    if not epd:
        raise DatabaseItemNotFound(f"Could not find EPD with id: {origin_id}")

    project_epd = models_epd.ProjectEPD.create_from_epd(epd, project_id=project_id)
    session.add(project_epd)

    await session.commit()
    await session.refresh(project_epd)
    return project_epd


async def update_project_epd_mutation(
    info: Info,
    id: str,
    kg_per_m3: float | None = None,
    kg_per_m2: float | None = None,
    thickness: float | None = None,
) -> "GraphQLProjectEPD":
    session = info.context.get("session")
    project_epd = await session.get(models_epd.ProjectEPD, id)
    if not project_epd:
        raise DatabaseItemNotFound(f"Could not find Project EPD with id: {id}")

    kwargs = {"kg_per_m3": kg_per_m3, "kg_per_m2": kg_per_m2, "thickness": thickness}
    for key, value in kwargs.items():
        if value:
            setattr(project_epd, key, value)

    session.add(project_epd)

    await session.commit()
    await session.refresh(project_epd)
    return project_epd


async def delete_project_epd_mutation(info: Info, id: str) -> str:
    """Delete a project EPD"""

    session = info.context.get("session")
    project_epd = await session.get(models_epd.ProjectEPD, id)

    await session.delete(project_epd)
    await session.commit()
    return id


@strawberry.type
class GraphQLEPDBase:
    id: str
    name: str
    category: str
    gwp_by_phases: JSON
    odp_by_phases: JSON
    ap_by_phases: JSON
    ep_by_phases: JSON
    pocp_by_phases: JSON
    penre_by_phases: JSON
    pere_by_phases: JSON
    version: str
    unit: str | None
    expiration_date: date
    date_updated: date
    source: str
    source_data: str
    owner: str
    region: str
    type: str

    @strawberry.field
    def gwp(self, phases: list[str] | None = None) -> float:
        return schema_assembly.calculate_indicator(self.gwp_by_phases, phases)

    @strawberry.field
    def odp(self, phases: list[str] | None = None) -> float:
        return schema_assembly.calculate_indicator(self.odp_by_phases, phases)

    @strawberry.field
    def ap(self, phases: list[str] | None = None) -> float:
        return schema_assembly.calculate_indicator(self.ap_by_phases, phases)

    @strawberry.field
    def ep(self, phases: list[str] | None = None) -> float:
        return schema_assembly.calculate_indicator(self.ep_by_phases, phases)

    @strawberry.field
    def pocp(self, phases: list[str] | None = None) -> float:
        return schema_assembly.calculate_indicator(self.pocp_by_phases, phases)

    def penre(self, phases: list[str] | None = None) -> float:
        return schema_assembly.calculate_indicator(self.penre_by_phases, phases)

    def pere(self, phases: list[str] | None = None) -> float:
        return schema_assembly.calculate_indicator(self.pere_by_phases, phases)


@strawberry.type
class GraphQLEPD(GraphQLEPDBase):
    origin_id: str | None


@strawberry.federation.type(directives=[Keys(fields="project_id")])
class GraphQLProjectEPD(GraphQLEPDBase):
    origin_id: str
    kg_per_m3: float | None
    kg_per_m2: float | None
    thickness: float | None

    assemblies: list["schema_assembly.GraphQLAssembly"] | None
    project_id: strawberry.ID = strawberry.federation.field(external=True)

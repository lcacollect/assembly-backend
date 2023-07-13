import base64
import logging
import strawberry
from datetime import date
from enum import Enum
from sqlalchemy import func
from sqlmodel import select
from strawberry import UNSET
from strawberry.types import Info
from typing import Optional

import models.epd as models_epd
import schema.assembly as schema_assembly
from lcacollect_config.context import get_session
from lcacollect_config.exceptions import DatabaseItemNotFound
from lcacollect_config.graphql.input_filters import filter_model_query, sort_model_query
from lcacollect_config.graphql.pagination import Connection, Cursor, Edge, PageInfo
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
    """Query the database for EPD entries for a specific project."""

    session = get_session(info)

    query = select(models_epd.ProjectEPD).where(models_epd.ProjectEPD.project_id == project_id)

    if not filters:
        epds = await session.exec(query)
        return epds.all()
    else:
        query = filter_model_query(models_epd.ProjectEPD, filters, query=query)
        epds = await session.exec(query)
        return epds.all()


async def add_project_epds_mutation(info: Info, project_id: str, epd_ids: list[str]) -> list["GraphQLProjectEPD"]:
    """Add Global EPDs to a project."""
    session = get_session(info)

    project_epds = []
    for origin_id in epd_ids:
        epd = await session.get(models_epd.EPD, origin_id)
        if not epd:
            raise DatabaseItemNotFound(f"Could not find EPD with id: {origin_id}")

        project_epd = models_epd.ProjectEPD.create_from_epd(epd, project_id=project_id)
        project_epds.append(project_epd)
        session.add(project_epd)

    await session.commit()
    [await session.refresh(project_epd) for project_epd in project_epds]
    return project_epds


async def delete_project_epd_mutation(info: Info, id: str) -> str:
    """Delete a project EPD"""

    session = info.context.get("session")
    project_epd = await session.get(models_epd.ProjectEPD, id)

    await session.delete(project_epd)
    await session.commit()
    return id


@strawberry.enum
class GraphQLUnit(Enum):
    M = "M"
    M2 = "M2"
    M3 = "M3"
    kg = "KG"
    Tones = "Tones"
    PCS = "PCS"
    L = "L"
    M2R1 = "M2R1"
    UNKNOWN = "UNKNOWN"


@strawberry.type
class GraphQLConversion:
    to: GraphQLUnit
    value: float


@strawberry.type
class GraphQLImpactCategories:
    a1a3: float | None
    a4: float | None
    a5: float | None
    b1: float | None
    b2: float | None
    b3: float | None
    b4: float | None
    b5: float | None
    b6: float | None
    b7: float | None
    c1: float | None
    c2: float | None
    c3: float | None
    c4: float | None
    d: float | None


@strawberry.enum
class GraphQLImpactCategory(Enum):
    a1a3 = "a1a3"
    a4 = "a4"
    a5 = "a5"
    b1 = "b1"
    b2 = "b2"
    b3 = "b3"
    b4 = "b4"
    b5 = "b5"
    b6 = "b6"
    b7 = "b7"
    c1 = "c1"
    c2 = "c2"
    c3 = "c3"
    c4 = "c4"
    d = "d"


@strawberry.type
class GraphQLEPDBase:
    id: str
    name: str
    version: str
    declared_unit: str | None
    valid_until: date
    published_date: date
    source: str
    location: str
    subtype: str
    reference_service_life: int | None
    comment: str | None

    @strawberry.field
    def conversions(self) -> list[GraphQLConversion]:
        if not self.conversions:
            return []
        return [GraphQLConversion(**conversion) for conversion in self.conversions]

    @strawberry.field
    def gwp(self) -> GraphQLImpactCategories | None:
        if not self.gwp:
            return None
        return GraphQLImpactCategories(**self.gwp)

    @strawberry.field
    def odp(self) -> GraphQLImpactCategories | None:
        if not self.odp:
            return None
        return GraphQLImpactCategories(**self.odp)

    @strawberry.field
    def ap(self) -> GraphQLImpactCategories | None:
        if not self.ap:
            return None
        return GraphQLImpactCategories(**self.ap)

    @strawberry.field
    def ep(self) -> GraphQLImpactCategories | None:
        if not self.ep:
            return None
        return GraphQLImpactCategories(**self.ep)

    @strawberry.field
    def pocp(self) -> GraphQLImpactCategories | None:
        if not self.pocp:
            return None
        return GraphQLImpactCategories(**self.pocp)

    @strawberry.field
    def penre(self) -> GraphQLImpactCategories | None:
        if not self.penre:
            return None
        return GraphQLImpactCategories(**self.penre)

    @strawberry.field
    def pere(self) -> GraphQLImpactCategories | None:
        if not self.pere:
            return None
        return GraphQLImpactCategories(**self.pere)


@strawberry.type
class GraphQLEPD(GraphQLEPDBase):
    origin_id: str | None


@strawberry.federation.type(directives=[Keys(fields="project_id")])
class GraphQLProjectEPD(GraphQLEPDBase):
    origin_id: str

    assemblies: list["schema_assembly.GraphQLAssembly"] | None
    project_id: strawberry.ID = strawberry.federation.field(shareable=True)

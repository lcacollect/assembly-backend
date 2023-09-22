from inspect import getdoc

import strawberry
from lcacollect_config.graphql.pagination import Connection
from lcacollect_config.permissions import IsAuthenticated

import schema.assembly as schema_assembly
import schema.assembly_layer as schema_assembly_layer
import schema.epd as schema_epd
from core import federation
from core.permissions import IsAdmin


@strawberry.type
class Query:
    # assemblies: list[schema_assembly.GraphQLAssembly] = strawberry.field(
    #     permission_classes=[IsAuthenticated], resolver=schema_assembly.assemblies_query
    # )
    project_assemblies: list[schema_assembly.GraphQLProjectAssembly] = strawberry.field(
        permission_classes=[IsAuthenticated], resolver=schema_assembly.project_assemblies_query
    )

    epds: Connection[schema_epd.GraphQLEPD] = strawberry.field(resolver=schema_epd.epds_query)

    project_epds: list[schema_epd.GraphQLProjectEPD] = strawberry.field(
        permission_classes=[IsAuthenticated], resolver=schema_epd.project_epds_query
    )


@strawberry.type
class Mutation:
    # EPD
    add_project_epds: list[schema_epd.GraphQLProjectEPD] = strawberry.mutation(
        permission_classes=[IsAuthenticated],
        resolver=schema_epd.add_project_epds_mutation,
        description=getdoc(schema_epd.add_project_epds_mutation),
    )
    delete_project_epds: list[str] = strawberry.mutation(
        permission_classes=[IsAuthenticated],
        resolver=schema_epd.delete_project_epds_mutation,
        description=getdoc(schema_epd.delete_project_epds_mutation),
    )

    add_epds: list[schema_epd.GraphQLEPD] = strawberry.mutation(
        permission_classes=[IsAdmin],
        resolver=schema_epd.add_epds_mutation,
        description=getdoc(schema_epd.add_epds_mutation),
    )
    delete_epds: list[str] = strawberry.mutation(
        permission_classes=[IsAdmin],
        resolver=schema_epd.delete_epds_mutation,
        description=getdoc(schema_epd.delete_epds_mutation),
    )

    # Assembly
    add_project_assemblies: list[schema_assembly.GraphQLProjectAssembly] = strawberry.mutation(
        permission_classes=[IsAuthenticated],
        resolver=schema_assembly.add_project_assemblies_mutation,
    )
    delete_project_assemblies: list[str] = strawberry.mutation(
        permission_classes=[IsAuthenticated],
        resolver=schema_assembly.delete_project_assemblies_mutation,
    )
    update_project_assemblies: list[schema_assembly.GraphQLProjectAssembly] = strawberry.mutation(
        permission_classes=[IsAuthenticated],
        resolver=schema_assembly.update_project_assemblies_mutation,
    )
    # Assembly Layers
    add_project_assembly_layers: list[schema_assembly_layer.GraphQLAssemblyLayer] = strawberry.mutation(
        permission_classes=[IsAuthenticated],
        resolver=schema_assembly_layer.add_project_assembly_layers_mutation,
    )
    delete_project_assembly_layers: list[str] = strawberry.mutation(
        permission_classes=[IsAuthenticated],
        resolver=schema_assembly_layer.delete_project_assembly_layers_mutation,
    )
    update_project_assembly_layers: list[schema_assembly_layer.GraphQLAssemblyLayer] = strawberry.mutation(
        permission_classes=[IsAuthenticated],
        resolver=schema_assembly_layer.update_project_assembly_layers_mutation,
    )


schema = strawberry.federation.Schema(
    query=Query,
    mutation=Mutation,
    enable_federation_2=True,
    types=[schema_epd.GraphQLEPDBase, federation.GraphQLSchemaElement],
)

import os

from lcacollect_config.fastapi import get_context
from strawberry.fastapi import GraphQLRouter

from schema import schema

graphql_app = GraphQLRouter(
    schema,
    context_getter=get_context,
    path="/graphql",
    graphiql=os.getenv("SERVER_NAME") == "LCA Test",
)

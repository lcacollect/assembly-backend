#! /usr/bin/bash
set -e

# Make sure the folder exist
mkdir -p graphql

export SERVER_NAME="LCA Test"
export SERVER_HOST="http://test"
export PROJECT_NAME="LCA Test"
export POSTGRES_HOST=localhost
export POSTGRES_USER=postgresuser
export POSTGRES_PASSWORD=PLACEHOLDER
export POSTGRES_DB=project
export POSTGRES_PORT=5433
export AAD_OPENAPI_CLIENT_ID=PLACEHOLDER
export AAD_APP_CLIENT_ID=PLACEHOLDER
export AAD_TENANT_ID=PLACEHOLDER
export AAD_APP_GRAPH_SECRET=PLACEHOLDER
export ROUTER_URL=http://router.url
export INTERNAL_EMAIL_DOMAINS_LIST=arkitema,cowi,cowicloud
export SENDGRID_SECRET=PLACEHOLDER

# Export GraphQL schema
BASEDIR=$(dirname $0)
echo "Exporting GraphQL schema to: $BASEDIR/graphql/schema.graphql"
strawberry export-schema --app-dir $BASEDIR/src schema > $BASEDIR/graphql/schema.graphql

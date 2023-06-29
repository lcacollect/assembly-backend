import logging.config
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from lcacollect_config.security import azure_scheme

from core.config import settings
from initial_data.load_tabel7 import load as load_table_7_epds
from routes import graphql_app

if settings.SERVER_NAME != "LCA Test":
    logging.config.fileConfig("logging.conf", disable_existing_loggers=False)

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.SERVER_NAME,
    openapi_url=f"{settings.API_STR}/openapi.json",
    swagger_ui_oauth2_redirect_url="/oauth2-redirect",
    swagger_ui_init_oauth={
        "usePkceWithAuthorizationCodeGrant": True,
        "clientId": settings.AAD_OPENAPI_CLIENT_ID,
    },
)

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(graphql_app, prefix=settings.API_STR)


@app.on_event("startup")
async def app_init():
    """Initialize application services"""

    logger.info("Setting up Azure AD")
    # Setup Azure AD
    await azure_scheme.openid_config.load_config()

    # Load Table 7 EPDs
    if settings.SERVER_NAME != "LCA Test":
        table7_csv = Path(__file__).parent / "initial_data" / "BR18_bilag_2_tabel_7_version_2_201222.csv"
        await load_table_7_epds(table7_csv)

from lcacollect_config.config import AzureSettings, PostgresSettings, ServerSettings
from pydantic import AnyHttpUrl


class AssemblySettings(ServerSettings, AzureSettings, PostgresSettings):
    ROUTER_URL: AnyHttpUrl


settings = AssemblySettings()

from lcacollect_config.config import AzureSettings, PostgresSettings, ServerSettings


class AssemblySettings(ServerSettings, AzureSettings, PostgresSettings):
    pass


settings = AssemblySettings()

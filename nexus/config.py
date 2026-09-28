from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
    app_name: str = "NEXUS-100 AI Agent OS"
    environment: str = "development"
    api_token: str | None = None
    max_orchestrator_hops: int = 10
    max_agent_depth: int = 6
    max_retries: int = 3
    task_timeout_seconds: int = 900
    model_config = SettingsConfigDict(env_prefix="NEXUS_", env_file=".env", extra="ignore")
settings = Settings()

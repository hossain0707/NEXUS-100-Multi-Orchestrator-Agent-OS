from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "NEXUS-100 AI Agent OS"
    environment: str = "development"
    api_token: str | None = None
    database_url: str = "sqlite+aiosqlite:///./nexus.db"
    redis_url: str | None = None
    llm_base_url: str = "https://api.openai.com/v1"
    llm_api_key: str | None = None
    llm_model: str = "gpt-5.6"
    github_token: str | None = None
    max_orchestrator_hops: int = 10
    max_agent_depth: int = 6
    max_retries: int = 3
    task_timeout_seconds: int = 900
    model_config = SettingsConfigDict(env_prefix="NEXUS_", env_file=".env", extra="ignore")

    @model_validator(mode="after")
    def production_guards(self):
        if self.environment == "production" and not self.api_token:
            raise ValueError("NEXUS_API_TOKEN is required in production")
        return self


settings = Settings()

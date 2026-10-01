from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "NEXUS-100 AI Agent OS"
    environment: str = "development"
    api_token: str | None = None

    # Cloud Run containers have a writable /tmp filesystem. This default keeps
    # zero-config deployments bootable; production should override this with
    # a durable PostgreSQL/Cloud SQL URL.
    database_url: str = "sqlite+aiosqlite:////tmp/nexus.db"
    redis_url: str | None = None
    github_token: str | None = None

    max_orchestrator_hops: int = 10
    max_agent_depth: int = 6
    max_retries: int = 3
    task_timeout_seconds: int = 900

    # Adaptive model routing. The aliases are intentionally provider-neutral:
    # operators map them to concrete model IDs through environment variables.
    model_routing_enabled: bool = True
    backend_model_execution_enabled: bool = False
    model_fast: str = "fast"
    model_balanced: str = "balanced"
    model_strong: str = "strong"
    model_premium: str = "premium"
    max_model_escalations: int = 2

    max_output_tokens_low: int = 800
    max_output_tokens_medium: int = 1600
    max_output_tokens_high: int = 3200
    max_output_tokens_extra_high: int = 6000

    # Optional OpenAI-compatible backend. ChatGPT-hosted MCP usage does not
    # require this and NEXUS cannot change the model selected in the ChatGPT UI.
    llm_base_url: str = "https://api.openai.com/v1"
    llm_api_key: str | None = None
    llm_reasoning_parameter: str | None = None

    model_config = SettingsConfigDict(
        env_prefix="NEXUS_",
        env_file=".env",
        extra="ignore",
    )

    @model_validator(mode="after")
    def production_guards(self):
        if self.environment == "production" and not self.api_token:
            raise ValueError("NEXUS_API_TOKEN is required in production")

        if self.backend_model_execution_enabled and not self.api_token:
            raise ValueError(
                "NEXUS_API_TOKEN is required when backend model execution is enabled"
            )

        if self.backend_model_execution_enabled and not self.llm_api_key:
            raise ValueError(
                "NEXUS_LLM_API_KEY is required when backend model execution is enabled"
            )

        models = {
            self.model_fast,
            self.model_balanced,
            self.model_strong,
            self.model_premium,
        }
        if self.backend_model_execution_enabled and len(models) < 2:
            raise ValueError(
                "Configure at least two distinct model IDs for adaptive execution"
            )

        return self


settings = Settings()

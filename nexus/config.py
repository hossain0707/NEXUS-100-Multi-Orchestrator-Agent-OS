from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "NEXUS-100 AI Agent OS"
    environment: str = "development"
    api_token: str | None = None
    # Optional separate bearer token for private MCP deployments. Leave unset for
    # the public read-only directory MCP endpoint.
    mcp_api_token: str | None = None

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
    model_fast: str = "gpt-6-luna"
    model_balanced: str = "gpt-5.6-terra"
    model_strong: str = "gpt-6.1-sol"
    model_premium: str = "gpt-6-astra"
    model_discovery_enabled: bool = True
    model_catalog_ttl_seconds: int = 3600
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

    # Explicitly opt-in single-request Gemini smoke check; defaults safe/off.
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash-lite"
    gemini_smoke_enabled: bool = False
    gemini_free_tier_ack: bool = False

    # Set this only after the OpenAI plugin submission portal generates a
    # domain-verification token. The public challenge route returns it verbatim.
    openai_apps_challenge: str | None = None

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

        if self.gemini_smoke_enabled and not (
            self.api_token and self.gemini_free_tier_ack and self.gemini_api_key
        ):
            raise ValueError(
                "Gemini smoke requires REST auth token, free-tier acknowledgement, "
                "and Gemini API key"
            )
        if self.gemini_smoke_enabled and self.gemini_model not in {
            "gemini-2.5-flash-lite", "gemini-2.5-flash"
        }:
            raise ValueError("Gemini smoke model must be on the limited allowlist")

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

from typing import Tuple, Type

from pydantic_settings import (
    BaseSettings,
    DotEnvSettingsSource,
    EnvSettingsSource,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    secret_key: str = "secret_key"
    debug: bool = False

    # Redis settings
    redis_url: str | None = "redis://redis:6379/0"
    redis_max_connections: int | None = 50

    # NATS settings
    nats_url: str | None = "nats://nats:4222"

    # OpenAI settings
    openai_model: str | None = "gpt-4.1"
    openai_api_key: str = "openai_api_key"
    openai_embedding_model: str | None = "text-embedding-3-large"
    openai_base_url: str | None = "https://api.openai.com/v1"

    # Google model settings
    gemini_model: str | None = "gemini-2.0-flash-001"
    gemini_api_key: str | None = "gemini_api_key"

    # Anthropic model settings
    anthropic_model: str | None = "claude-3-7-sonnet-latest"
    anthropic_api_key: str | None = "anthropic_api_key"
    anthropic_base_url: str | None = "https://api.anthropic.com/v1"

    # OLTP settings
    postgres_user: str | None = "pg-user-name"
    postgres_password: str | None = "pg-password"
    postgres_db: str | None = "pg-match-db-name"
    postgres_uri: str | None = "pg-match-uri"

    # Neo4j settings
    neo4j_bolt_url: str | None = "bolt://neo4j:1234@neo4j:7687/match"
    neo4j_max_connections: int = 10
    neo4j_connection_timeout: int = 60
    neo4j_max_connection_lifetime: int = 3600

    # Campaign settings
    campaign_webhook_url: str | None = None

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        source = [
            init_settings,
            EnvSettingsSource(
                settings_cls,
            ),
            DotEnvSettingsSource(
                settings_cls,
                ".env",
            ),
            file_secret_settings,
        ]

        return (*source,)

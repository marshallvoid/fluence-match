from functools import lru_cache

from match.config.settings import Settings


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

__all__ = ["get_settings", "Settings"]

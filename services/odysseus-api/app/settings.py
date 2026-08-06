from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    environment: str = "development"
    nats_url: str = "nats://localhost:4222"
    search_profiles_path: str = "/app/config/search_profiles.yml"
    nats_subject: str = "odysseus.jobs.search"
    nats_result_subject: str = "odysseus.results.search"
    nats_stream: str = "ODYSSEUS_SEARCH"

    model_config = SettingsConfigDict(env_prefix="ODYSSEUS_", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()

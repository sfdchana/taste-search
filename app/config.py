"""Typed application config.

Decision: config is loaded from the environment (a .env file locally, real
env vars in prod) into a typed Settings object. If DATABASE_URL is missing the
app refuses to start — fail fast at boot, never mid-request. This is the same
schema-first instinct as the database: the config has a contract too.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str


settings = Settings()

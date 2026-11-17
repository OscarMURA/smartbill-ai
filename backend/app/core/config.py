"""Application settings sourced from the environment."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "SmartBill AI"
    environment: str = "development"
    database_url: str = "sqlite:///./smartbill.db"
    frontend_origin: str = "http://localhost:5173"
    public_demo: bool = False
    session_cookie_secure: bool = False
    llm_base_url: str = "https://inference.do-ai.run/v1"
    llm_api_key: str | None = None
    llm_model: str = "glm-5.3"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

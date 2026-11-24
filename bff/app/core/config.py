from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="BFF_", extra="ignore")

    system_url: str = "http://127.0.0.1:8001"  # the system backend (all business logic)


settings = Settings()

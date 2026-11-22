from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).resolve().parents[1] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_ENV_FILE, extra="ignore")

    database_url: str = "sqlite:///./app.db"
    keitaro_api_key: str = ""
    keitaro_admin_url: str = ""
    keitaro_api_url: str = ""
    keitaro_domain_name: str = ""
    keitaro_domain_id: int = 0
    keitaro_group_name: str = ""
    keitaro_group_id: int = 0
    keitaro_source_name: str = ""
    keitaro_source_id: int = 0
    keitaro_mock: bool = False


settings = Settings()
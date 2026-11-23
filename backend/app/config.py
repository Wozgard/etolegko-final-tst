from pathlib import Path
from typing import Self

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parents[1]
_ENV_FILE = _BACKEND_DIR / ".env"


def mock_database_path() -> Path:
    return _BACKEND_DIR / "app.mock.db"


def production_database_path() -> Path:
    return _BACKEND_DIR / "app.db"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_ENV_FILE, extra="ignore")

    database_url: str = ""
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

    @model_validator(mode="after")
    def _resolve_database_url(self) -> Self:
        path = mock_database_path() if self.keitaro_mock else production_database_path()
        self.database_url = f"sqlite:///{path.as_posix()}"
        return self


settings = Settings()
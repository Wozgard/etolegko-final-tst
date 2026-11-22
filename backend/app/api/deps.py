from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.config import Settings, settings
from app.db import SessionLocal
from app.mocks.keitaro_mock_client import MockKeitaroClient
from app.services.keitaro_client import HttpxKeitaroClient, KeitaroClient

_mock_client: MockKeitaroClient | None = None


def get_settings() -> Settings:
    return settings


def get_keitaro_client(
    app_settings: Annotated[Settings, Depends(get_settings)],
) -> KeitaroClient:
    global _mock_client
    if app_settings.keitaro_mock:
        if _mock_client is None:
            _mock_client = MockKeitaroClient()
        return _mock_client
    return HttpxKeitaroClient(app_settings.keitaro_api_url, app_settings.keitaro_api_key)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
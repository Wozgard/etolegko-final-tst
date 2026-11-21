from typing import Annotated

from fastapi import Depends

from app.config import Settings, settings
from app.services.keitaro_client import HttpxKeitaroClient, KeitaroClient


def get_settings() -> Settings:
    return settings


def get_keitaro_client(
    app_settings: Annotated[Settings, Depends(get_settings)],
) -> KeitaroClient:
    return HttpxKeitaroClient(app_settings.keitaro_api_url, app_settings.keitaro_api_key)
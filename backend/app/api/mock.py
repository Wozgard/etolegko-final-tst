from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_keitaro_client, get_settings
from app.config import Settings
from app.mocks.keitaro_mock_client import MockKeitaroClient, load_remove_offer_ids
from app.services.keitaro_client import KeitaroClient

router = APIRouter(tags=["mock"])


@router.post("/mock/remove-offers")
def remove_marked_offers(
    app_settings: Annotated[Settings, Depends(get_settings)],
    keitaro_client: Annotated[KeitaroClient, Depends(get_keitaro_client)],
) -> dict[str, list[dict[str, int]]]:
    if not app_settings.keitaro_mock:
        raise HTTPException(status_code=404, detail="Not available without keitaro mock")
    if not isinstance(keitaro_client, MockKeitaroClient):
        raise HTTPException(status_code=404, detail="Not available without keitaro mock")
    offer_ids = load_remove_offer_ids()
    removed = keitaro_client.remove_offers_from_streams(offer_ids)
    return {"removed": removed}
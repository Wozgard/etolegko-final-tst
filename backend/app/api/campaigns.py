from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_keitaro_client, get_settings
from app.config import Settings
from app.domain.campaign import CAMPAIGN_NAME_PREFIX
from app.schemas.campaign import CampaignListItem, CreateCampaignRequest, CreateCampaignResponse, OfferListItem
from app.services.create_campaign import CreateCampaignError, create_campaign
from app.services.keitaro_client import KeitaroClient

router = APIRouter()


@router.get("/offers", response_model=list[OfferListItem])
def get_offers(
    keitaro: Annotated[KeitaroClient, Depends(get_keitaro_client)],
    q: str = "",
) -> list[OfferListItem]:
    if not q:
        return []
    needle = q.casefold()
    result: list[OfferListItem] = []
    for offer in keitaro.list_offers():
        offer_id = offer.get("id")
        name = offer.get("name")
        if not isinstance(offer_id, int) or not isinstance(name, str):
            continue
        if needle in str(offer_id).casefold() or needle in name.casefold():
            result.append(OfferListItem(id=offer_id, name=name))
    return result


@router.get("/campaigns", response_model=list[CampaignListItem])
def get_campaigns(
    keitaro: Annotated[KeitaroClient, Depends(get_keitaro_client)],
) -> list[CampaignListItem]:
    return [
        CampaignListItem(id=campaign["id"], name=campaign["name"])
        for campaign in keitaro.list_campaigns()
        if isinstance(campaign.get("name"), str) and campaign["name"].startswith(CAMPAIGN_NAME_PREFIX)
    ]


@router.post("/campaigns", status_code=status.HTTP_201_CREATED, response_model=CreateCampaignResponse)
def post_create_campaign(
    body: CreateCampaignRequest,
    app_settings: Annotated[Settings, Depends(get_settings)],
    keitaro: Annotated[KeitaroClient, Depends(get_keitaro_client)],
) -> CreateCampaignResponse:
    try:
        campaign_id = create_campaign(
            keitaro,
            app_settings,
            name=body.name,
            geo=body.geo,
            offer_id=body.offer_id,
        )
    except CreateCampaignError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from exc

    return CreateCampaignResponse(id=campaign_id)
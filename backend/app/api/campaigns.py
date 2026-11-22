from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_keitaro_client, get_settings
from app.config import Settings
from app.domain.campaign import CAMPAIGN_NAME_PREFIX
from app.models import Base
from app.db import engine
from app.schemas.campaign import (
    CampaignListItem,
    CreateCampaignRequest,
    CreateCampaignResponse,
    OfferListItem,
    PushCampaignOffersRequest,
)
from app.services.campaign_offers import list_campaign_streams_response, push_campaign_offers
from app.services.create_campaign import CreateCampaignError, create_campaign
from app.services.keitaro_client import KeitaroClient

router = APIRouter()

Base.metadata.create_all(bind=engine)


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


@router.get("/campaigns/{campaign_id}/streams")
def get_campaign_streams(
    campaign_id: int,
    keitaro: Annotated[KeitaroClient, Depends(get_keitaro_client)],
    db: Annotated[Session, Depends(get_db)],
) -> list[dict[str, Any]]:
    return list_campaign_streams_response(keitaro, db, campaign_id)


@router.post("/campaigns/{campaign_id}/push", status_code=status.HTTP_204_NO_CONTENT)
def post_push_campaign_offers(
    campaign_id: int,
    body: PushCampaignOffersRequest,
    keitaro: Annotated[KeitaroClient, Depends(get_keitaro_client)],
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    try:
        push_campaign_offers(
            keitaro,
            db,
            campaign_id,
            [offer.model_dump() for offer in body.offers],
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)
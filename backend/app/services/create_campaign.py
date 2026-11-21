from __future__ import annotations

from typing import Any

from app.config import Settings
from app.domain.campaign import campaign_alias, normalize_campaign_name
from app.services.keitaro_client import KeitaroClient


class CreateCampaignError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


def _domain_name(entry: dict[str, Any]) -> str | None:
    for key in ("name", "domain"):
        value = entry.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def _verify_domain(client: KeitaroClient, settings: Settings) -> None:
    for entry in client.list_domains():
        if entry.get("id") == settings.keitaro_domain_id:
            if _domain_name(entry) == settings.keitaro_domain_name:
                return
    raise CreateCampaignError("Configured Keitaro domain was not found")


def _verify_group(client: KeitaroClient, settings: Settings) -> None:
    for entry in client.list_groups():
        if entry.get("id") == settings.keitaro_group_id and entry.get("name") == settings.keitaro_group_name:
            return
    raise CreateCampaignError("Configured Keitaro campaign group was not found")


def _verify_traffic_source(client: KeitaroClient, settings: Settings) -> None:
    source = client.get_traffic_source(settings.keitaro_source_id)
    if source and source.get("name") == settings.keitaro_source_name:
        return
    raise CreateCampaignError("Configured Keitaro traffic source was not found")


def _verify_offer(client: KeitaroClient, offer_id: int) -> None:
    if client.get_offer(offer_id) is not None:
        return
    raise CreateCampaignError("Offer was not found in Keitaro")


def _ensure_unique_name(client: KeitaroClient, name: str) -> None:
    for campaign in client.list_campaigns():
        if campaign.get("name") == name:
            raise CreateCampaignError("Campaign with this name already exists")


def _build_campaign_payload(name: str, settings: Settings) -> dict[str, Any]:
    return {
        "name": name,
        "alias": campaign_alias(name),
        "type": "position",
        "domain_id": settings.keitaro_domain_id,
        "group_id": str(settings.keitaro_group_id),
        "traffic_source_id": settings.keitaro_source_id,
    }


def _build_geo_stream(campaign_id: int, geo: str) -> dict[str, Any]:
    return {
        "campaign_id": campaign_id,
        "type": "regular",
        "position": 1,
        "name": "geo",
        "schema": "redirect",
        "action_type": "http",
        "action_payload": "https://www.google.com",
        "filters": [
            {
                "name": "country",
                "mode": "accept",
                "payload": [geo.upper()],
            }
        ],
    }


def _build_offer_stream(campaign_id: int, offer_id: int) -> dict[str, Any]:
    return {
        "campaign_id": campaign_id,
        "type": "regular",
        "position": 2,
        "name": "offer",
        "schema": "landings",
        "action_type": "http",
        "offers": [
            {
                "offer_id": offer_id,
                "share": 100,
                "state": "active",
            }
        ],
    }


def create_campaign(
    client: KeitaroClient,
    settings: Settings,
    *,
    name: str,
    geo: str,
    offer_id: int,
) -> int:
    if not settings.keitaro_api_url:
        raise CreateCampaignError("Keitaro API URL is not configured")

    final_name = normalize_campaign_name(name)

    _ensure_unique_name(client, final_name)
    _verify_domain(client, settings)
    _verify_group(client, settings)
    _verify_traffic_source(client, settings)
    _verify_offer(client, offer_id)

    created = client.create_campaign(_build_campaign_payload(final_name, settings))
    campaign_id = created.get("id")
    if not isinstance(campaign_id, int):
        raise CreateCampaignError("Keitaro returned campaign without id")

    client.create_stream(_build_geo_stream(campaign_id, geo))
    client.create_stream(_build_offer_stream(campaign_id, offer_id))
    return campaign_id
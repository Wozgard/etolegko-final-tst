from __future__ import annotations

from copy import deepcopy
from typing import Any


class FakeKeitaroClient:
    def __init__(
        self,
        *,
        domains: list[dict[str, Any]] | None = None,
        groups: list[dict[str, Any]] | None = None,
        traffic_source: dict[str, Any] | None = None,
        offers: dict[int, dict[str, Any]] | None = None,
        campaigns: list[dict[str, Any]] | None = None,
    ) -> None:
        self.domains = domains or []
        self.groups = groups or []
        self.traffic_source = traffic_source
        self.offers = offers or {}
        self.campaigns = campaigns or []
        self.created_campaigns: list[dict[str, Any]] = []
        self.created_streams: list[dict[str, Any]] = []
        self._next_campaign_id = 1001

    def list_domains(self) -> list[dict[str, Any]]:
        return deepcopy(self.domains)

    def list_groups(self) -> list[dict[str, Any]]:
        return deepcopy(self.groups)

    def get_traffic_source(self, source_id: int) -> dict[str, Any] | None:
        if self.traffic_source is None:
            return None
        if self.traffic_source.get("id") != source_id:
            return None
        return deepcopy(self.traffic_source)

    def get_offer(self, offer_id: int) -> dict[str, Any] | None:
        offer = self.offers.get(offer_id)
        return deepcopy(offer) if offer else None

    def list_offers(self) -> list[dict[str, Any]]:
        return [deepcopy(offer) for offer in self.offers.values()]

    def list_campaigns(self) -> list[dict[str, Any]]:
        return deepcopy(self.campaigns)

    def create_campaign(self, payload: dict[str, Any]) -> dict[str, Any]:
        campaign = {"id": self._next_campaign_id, **deepcopy(payload)}
        self._next_campaign_id += 1
        self.created_campaigns.append(deepcopy(payload))
        self.campaigns.append(campaign)
        return deepcopy(campaign)

    def create_stream(self, payload: dict[str, Any]) -> dict[str, Any]:
        stream = {"id": len(self.created_streams) + 1, **deepcopy(payload)}
        self.created_streams.append(deepcopy(payload))
        return stream
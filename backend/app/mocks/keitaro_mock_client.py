from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

_SEED_PATH = Path(__file__).resolve().parent / "keitaro.json"


def _load_seed() -> dict[str, Any]:
    with _SEED_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def load_remove_offer_ids() -> list[int]:
    raw = _load_seed().get("remove_offers", [])
    return [offer_id for offer_id in raw if isinstance(offer_id, int)]


class MockKeitaroClient:
    def __init__(self, seed: dict[str, Any] | None = None) -> None:
        data = deepcopy(seed if seed is not None else _load_seed())
        self._domains: list[dict[str, Any]] = data.get("domains", [])
        self._groups: list[dict[str, Any]] = data.get("groups", [])
        self._traffic_source: dict[str, Any] | None = data.get("traffic_source")
        offers_raw = data.get("offers", [])
        self._offers: dict[int, dict[str, Any]] = {
            entry["id"]: entry for entry in offers_raw if isinstance(entry.get("id"), int)
        }
        self._campaigns: list[dict[str, Any]] = data.get("campaigns", [])
        streams_raw = data.get("streams_by_campaign", {})
        self._streams_by_campaign: dict[int, list[dict[str, Any]]] = {
            int(campaign_id): deepcopy(streams)
            for campaign_id, streams in streams_raw.items()
        }
        self._next_campaign_id = self._max_campaign_id() + 1
        self._next_stream_id = self._max_stream_id() + 1

    def _max_campaign_id(self) -> int:
        ids = [c["id"] for c in self._campaigns if isinstance(c.get("id"), int)]
        return max(ids, default=0)

    def _max_stream_id(self) -> int:
        ids: list[int] = []
        for streams in self._streams_by_campaign.values():
            for stream in streams:
                stream_id = stream.get("id")
                if isinstance(stream_id, int):
                    ids.append(stream_id)
        return max(ids, default=0)

    def list_domains(self) -> list[dict[str, Any]]:
        return deepcopy(self._domains)

    def list_groups(self) -> list[dict[str, Any]]:
        return deepcopy(self._groups)

    def get_traffic_source(self, source_id: int) -> dict[str, Any] | None:
        if self._traffic_source is None:
            return None
        if self._traffic_source.get("id") != source_id:
            return None
        return deepcopy(self._traffic_source)

    def get_offer(self, offer_id: int) -> dict[str, Any] | None:
        offer = self._offers.get(offer_id)
        return deepcopy(offer) if offer is not None else None

    def list_offers(self) -> list[dict[str, Any]]:
        return [deepcopy(offer) for offer in self._offers.values()]

    def list_campaigns(self) -> list[dict[str, Any]]:
        return deepcopy(self._campaigns)

    def create_campaign(self, payload: dict[str, Any]) -> dict[str, Any]:
        campaign = {"id": self._next_campaign_id, **deepcopy(payload)}
        self._next_campaign_id += 1
        self._campaigns.append(deepcopy(campaign))
        self._streams_by_campaign[campaign["id"]] = []
        return deepcopy(campaign)

    def create_stream(self, payload: dict[str, Any]) -> dict[str, Any]:
        stream = {"id": self._next_stream_id, **deepcopy(payload)}
        self._next_stream_id += 1
        campaign_id = stream.get("campaign_id")
        if isinstance(campaign_id, int):
            self._streams_by_campaign.setdefault(campaign_id, []).append(deepcopy(stream))
        return deepcopy(stream)

    def list_campaign_streams(self, campaign_id: int) -> list[dict[str, Any]]:
        streams = self._streams_by_campaign.get(campaign_id, [])
        return deepcopy(streams)

    def update_stream(self, stream_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        for campaign_streams in self._streams_by_campaign.values():
            for stream in campaign_streams:
                if stream.get("id") == stream_id:
                    stream.update(deepcopy(payload))
                    return deepcopy(stream)
        return {"id": stream_id, **deepcopy(payload)}

    def remove_offers_from_streams(self, offer_ids: list[int]) -> list[dict[str, int]]:
        targets = set(offer_ids)
        removed: list[dict[str, int]] = []
        for campaign_id, streams in self._streams_by_campaign.items():
            for stream in streams:
                offers = stream.get("offers")
                if not isinstance(offers, list):
                    continue
                stream_id = stream.get("id")
                if not isinstance(stream_id, int):
                    continue
                kept: list[dict[str, Any]] = []
                for entry in offers:
                    offer_id = entry.get("offer_id")
                    if isinstance(offer_id, int) and offer_id in targets:
                        removed.append(
                            {
                                "campaign_id": campaign_id,
                                "stream_id": stream_id,
                                "offer_id": offer_id,
                            }
                        )
                    else:
                        kept.append(entry)
                stream["offers"] = kept
        return removed
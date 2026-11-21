from __future__ import annotations

from copy import deepcopy
from typing import Any

from tests.fake_keitaro import FakeKeitaroClient


class EditorFakeKeitaroClient(FakeKeitaroClient):
    """Fake Keitaro client with stream read/update for the offer editor tests."""

    def __init__(
        self,
        *,
        streams_by_campaign: dict[int, list[dict[str, Any]]] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.streams_by_campaign = deepcopy(streams_by_campaign or {})
        self.updated_streams: list[dict[str, Any]] = []

    def list_campaign_streams(self, campaign_id: int) -> list[dict[str, Any]]:
        streams = self.streams_by_campaign.get(campaign_id, [])
        return deepcopy(streams)

    def update_stream(self, stream_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        record = {"stream_id": stream_id, **deepcopy(payload)}
        self.updated_streams.append(record)
        for campaign_streams in self.streams_by_campaign.values():
            for stream in campaign_streams:
                if stream.get("id") == stream_id:
                    stream.update(deepcopy(payload))
                    return deepcopy(stream)
        return record

    def set_stream_offers(self, stream_id: int, offers: list[dict[str, Any]]) -> None:
        for campaign_streams in self.streams_by_campaign.values():
            for stream in campaign_streams:
                if stream.get("id") == stream_id:
                    stream["offers"] = deepcopy(offers)
                    return
        raise KeyError(f"stream {stream_id} not found")
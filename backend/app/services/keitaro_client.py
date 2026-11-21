from __future__ import annotations

from typing import Any, Protocol

import httpx


class KeitaroClient(Protocol):
    def list_domains(self) -> list[dict[str, Any]]: ...

    def list_groups(self) -> list[dict[str, Any]]: ...

    def get_traffic_source(self, source_id: int) -> dict[str, Any] | None: ...

    def get_offer(self, offer_id: int) -> dict[str, Any] | None: ...

    def list_offers(self) -> list[dict[str, Any]]: ...

    def list_campaigns(self) -> list[dict[str, Any]]: ...

    def create_campaign(self, payload: dict[str, Any]) -> dict[str, Any]: ...

    def create_stream(self, payload: dict[str, Any]) -> dict[str, Any]: ...


class HttpxKeitaroClient:
    def __init__(self, api_url: str, api_key: str, client: httpx.Client | None = None) -> None:
        self._base_url = api_url.rstrip("/")
        self._headers = {"Api-Key": api_key, "Accept": "application/json"}
        self._client = client or httpx.Client(timeout=30.0)

    def _get(self, path: str) -> Any:
        response = self._client.get(f"{self._base_url}{path}", headers=self._headers)
        response.raise_for_status()
        return response.json()

    def _post(self, path: str, payload: dict[str, Any]) -> Any:
        response = self._client.post(
            f"{self._base_url}{path}",
            headers=self._headers,
            json=payload,
        )
        response.raise_for_status()
        return response.json()

    def list_domains(self) -> list[dict[str, Any]]:
        data = self._get("/domains")
        return data if isinstance(data, list) else []

    def list_groups(self) -> list[dict[str, Any]]:
        data = self._get("/groups?type=campaigns")
        return data if isinstance(data, list) else []

    def get_traffic_source(self, source_id: int) -> dict[str, Any] | None:
        try:
            return self._get(f"/traffic_sources/{source_id}")
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                return None
            raise

    def get_offer(self, offer_id: int) -> dict[str, Any] | None:
        try:
            return self._get(f"/offers/{offer_id}")
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                return None
            raise

    def list_offers(self) -> list[dict[str, Any]]:
        data = self._get("/offers")
        return data if isinstance(data, list) else []

    def list_campaigns(self) -> list[dict[str, Any]]:
        data = self._get("/campaigns")
        return data if isinstance(data, list) else []

    def create_campaign(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._post("/campaigns", payload)

    def create_stream(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._post("/streams", payload)
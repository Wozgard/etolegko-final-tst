from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.api import deps
from app.api.deps import get_settings
from app.config import Settings
from app.main import app
from app.mocks.keitaro_mock_client import MockKeitaroClient
from app.services.keitaro_client import HttpxKeitaroClient


def _mock_settings() -> Settings:
    return Settings(
        keitaro_mock=True,
        keitaro_api_url="https://example.test/admin_api/v1",
        keitaro_api_key="test-key",
        keitaro_domain_name="kylovoa.com",
        keitaro_domain_id=1813,
        keitaro_group_name="FORTESTS",
        keitaro_group_id=10332,
        keitaro_source_name="FORTESTS",
        keitaro_source_id=836,
    )


@pytest.fixture
def api_client() -> TestClient:
    deps._mock_client = None
    app.dependency_overrides[get_settings] = lambda: _mock_settings()
    client = TestClient(app)
    try:
        yield client
    finally:
        app.dependency_overrides.clear()
        deps._mock_client = None


def test_list_campaigns_uses_mock_seed_without_httpx_client(api_client: TestClient) -> None:
    with patch.object(HttpxKeitaroClient, "__init__", autospec=True) as httpx_init:
        response = api_client.get("/campaigns")

    httpx_init.assert_not_called()
    assert response.status_code == 200
    body = response.json()
    names = {item["name"] for item in body}
    assert "test_shvirev_alpha" in names
    assert "test_shvirev_beta" in names
    assert "other_campaign" not in names


def test_remove_offers_from_streams_keeps_other_offer_share() -> None:
    client = MockKeitaroClient(
        seed={
            "offers": [],
            "campaigns": [{"id": 10, "name": "demo"}],
            "streams_by_campaign": {
                "10": [
                    {
                        "id": 102,
                        "campaign_id": 10,
                        "name": "offer",
                        "offers": [
                            {"offer_id": 77, "share": 50, "state": "active"},
                            {"offer_id": 88, "share": 50, "state": "active"},
                        ],
                    },
                ],
            },
        },
    )

    removed = client.remove_offers_from_streams([77])

    assert removed == [{"campaign_id": 10, "stream_id": 102, "offer_id": 77}]
    streams = client.list_campaign_streams(10)
    offer_stream = next(stream for stream in streams if stream.get("name") == "offer")
    assert offer_stream["offers"] == [{"offer_id": 88, "share": 50, "state": "active"}]
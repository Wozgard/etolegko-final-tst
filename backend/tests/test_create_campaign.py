from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_keitaro_client, get_settings
from app.config import Settings
from app.main import app
from tests.fake_keitaro import FakeKeitaroClient


def _valid_settings() -> Settings:
    return Settings(
        keitaro_api_url="https://example.test/admin_api/v1",
        keitaro_api_key="test-key",
        keitaro_domain_name="kylovoa.com",
        keitaro_domain_id=1813,
        keitaro_group_name="FORTESTS",
        keitaro_group_id=10332,
        keitaro_source_name="FORTESTS",
        keitaro_source_id=836,
    )


def _valid_fake() -> FakeKeitaroClient:
    return FakeKeitaroClient(
        domains=[{"id": 1813, "name": "kylovoa.com"}],
        groups=[{"id": 10332, "name": "FORTESTS", "type": "campaigns"}],
        traffic_source={"id": 836, "name": "FORTESTS"},
        offers={77: {"id": 77, "name": "Sample Offer"}},
    )


@pytest.fixture
def api_client() -> TestClient:
    fake = _valid_fake()
    app_settings = _valid_settings()

    app.dependency_overrides[get_settings] = lambda: app_settings
    app.dependency_overrides[get_keitaro_client] = lambda: fake

    client = TestClient(app)
    try:
        yield client
    finally:
        app.dependency_overrides.clear()


def test_create_campaign_adds_prefix_to_short_name(api_client: TestClient) -> None:
    fake = app.dependency_overrides[get_keitaro_client]()
    assert isinstance(fake, FakeKeitaroClient)

    response = api_client.post(
        "/campaigns",
        json={"name": "campaign1", "geo": "us", "offer_id": 77},
    )

    assert response.status_code == 201
    assert response.json() == {"id": 1001}
    assert fake.created_campaigns[0]["name"] == "test_shvirev_campaign1"
    assert fake.created_campaigns[0]["alias"] == "test_shvirev_campaign1"


def test_create_campaign_keeps_existing_prefix(api_client: TestClient) -> None:
    fake = app.dependency_overrides[get_keitaro_client]()

    response = api_client.post(
        "/campaigns",
        json={"name": "test_shvirev_alpha", "geo": "us", "offer_id": 77},
    )

    assert response.status_code == 201
    assert fake.created_campaigns[0]["name"] == "test_shvirev_alpha"
    assert fake.created_campaigns[0]["alias"] == "test_shvirev_alpha"


def test_create_campaign_alias_from_final_name(api_client: TestClient) -> None:
    fake = app.dependency_overrides[get_keitaro_client]()

    response = api_client.post(
        "/campaigns",
        json={"name": "My Campaign", "geo": "de", "offer_id": 77},
    )

    assert response.status_code == 201
    assert fake.created_campaigns[0]["name"] == "test_shvirev_My Campaign"
    assert fake.created_campaigns[0]["alias"] == "test_shvirev_my_campaign"


@pytest.mark.parametrize(
    ("settings_override", "fake_override", "payload", "detail_substring"),
    [
        (
            {"keitaro_api_url": ""},
            {},
            {"name": "campaign1", "geo": "us", "offer_id": 77},
            "Keitaro API URL is not configured",
        ),
        (
            {},
            {"campaigns": [{"id": 1, "name": "test_shvirev_x"}]},
            {"name": "x", "geo": "us", "offer_id": 77},
            "already exists",
        ),
        (
            {},
            {"campaigns": [{"id": 1, "name": "test_shvirev_x"}]},
            {"name": "test_shvirev_x", "geo": "us", "offer_id": 77},
            "already exists",
        ),
        (
            {},
            {"domains": []},
            {"name": "campaign1", "geo": "us", "offer_id": 77},
            "domain was not found",
        ),
        (
            {},
            {"groups": [{"id": 10332, "name": "OTHER", "type": "campaigns"}]},
            {"name": "campaign1", "geo": "us", "offer_id": 77},
            "campaign group was not found",
        ),
        (
            {},
            {"traffic_source": {"id": 836, "name": "WRONG"}},
            {"name": "campaign1", "geo": "us", "offer_id": 77},
            "traffic source was not found",
        ),
        (
            {},
            {"offers": {}},
            {"name": "campaign1", "geo": "us", "offer_id": 77},
            "Offer was not found",
        ),
    ],
)
def test_create_campaign_validation_errors(
    settings_override: dict[str, Any],
    fake_override: dict[str, Any],
    payload: dict[str, Any],
    detail_substring: str,
) -> None:
    app_settings = _valid_settings().model_copy(update=settings_override)
    fake_kwargs: dict[str, Any] = {
        "domains": [{"id": 1813, "name": "kylovoa.com"}],
        "groups": [{"id": 10332, "name": "FORTESTS", "type": "campaigns"}],
        "traffic_source": {"id": 836, "name": "FORTESTS"},
        "offers": {77: {"id": 77, "name": "Sample Offer"}},
        "campaigns": [],
    }
    fake_kwargs.update(fake_override)
    fake = FakeKeitaroClient(**fake_kwargs)

    app.dependency_overrides[get_settings] = lambda: app_settings
    app.dependency_overrides[get_keitaro_client] = lambda: fake
    client = TestClient(app)

    try:
        response = client.post("/campaigns", json=payload)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 400
    assert detail_substring in response.json()["detail"]
    assert fake.created_campaigns == []
    assert fake.created_streams == []
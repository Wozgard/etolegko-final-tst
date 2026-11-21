from __future__ import annotations

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


@pytest.fixture
def api_client() -> TestClient:
    fake = FakeKeitaroClient(
        offers={
            77: {"id": 77, "name": "Alpha"},
            177: {"id": 177, "name": "Beta"},
        },
    )
    app_settings = _valid_settings()

    app.dependency_overrides[get_settings] = lambda: app_settings
    app.dependency_overrides[get_keitaro_client] = lambda: fake

    client = TestClient(app)
    try:
        yield client
    finally:
        app.dependency_overrides.clear()


def test_search_offers_q_77_returns_both(api_client: TestClient) -> None:
    response = api_client.get("/offers", params={"q": "77"})

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    ids = {item["id"] for item in body}
    assert ids == {77, 177}


def test_search_offers_q_177_returns_only_beta(api_client: TestClient) -> None:
    response = api_client.get("/offers", params={"q": "177"})

    assert response.status_code == 200
    assert response.json() == [{"id": 177, "name": "Beta"}]


def test_search_offers_empty_q_returns_empty(api_client: TestClient) -> None:
    response = api_client.get("/offers", params={"q": ""})

    assert response.status_code == 200
    assert response.json() == []
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
        campaigns=[
            {"id": 10, "name": "test_shvirev_alpha"},
            {"id": 20, "name": "other_campaign"},
        ],
    )
    app_settings = _valid_settings()

    app.dependency_overrides[get_settings] = lambda: app_settings
    app.dependency_overrides[get_keitaro_client] = lambda: fake

    client = TestClient(app)
    try:
        yield client
    finally:
        app.dependency_overrides.clear()


def test_list_campaigns_returns_only_prefixed(api_client: TestClient) -> None:
    response = api_client.get("/campaigns")

    assert response.status_code == 200
    body = response.json()
    names = [item["name"] for item in body]
    assert "test_shvirev_alpha" in names
    assert "other_campaign" not in names
    assert body == [{"id": 10, "name": "test_shvirev_alpha"}]
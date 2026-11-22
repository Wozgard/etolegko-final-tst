from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.api import deps
from app.api.deps import get_settings
from app.config import Settings
from app.main import app
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
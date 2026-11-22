from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_keitaro_client, get_settings
from app.config import Settings
from app.main import app
from tests.fake_keitaro_editor import EditorFakeKeitaroClient

CAMPAIGN_ID = 10
GEO_STREAM_ID = 101
OFFER_STREAM_ID = 102


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


def _base_streams(
    *,
    offer_entries: list[dict[str, object]],
) -> dict[int, list[dict[str, object]]]:
    return {
        CAMPAIGN_ID: [
            {
                "id": GEO_STREAM_ID,
                "campaign_id": CAMPAIGN_ID,
                "name": "geo",
                "schema": "redirect",
                "type": "regular",
            },
            {
                "id": OFFER_STREAM_ID,
                "campaign_id": CAMPAIGN_ID,
                "name": "offer",
                "schema": "landings",
                "type": "regular",
                "offers": offer_entries,
            },
        ],
    }


def _editor_fake(
    *,
    offer_entries: list[dict[str, object]] | None = None,
) -> EditorFakeKeitaroClient:
    entries = offer_entries or [{"offer_id": 77, "share": 100, "state": "active"}]
    return EditorFakeKeitaroClient(
        campaigns=[{"id": CAMPAIGN_ID, "name": "test_shvirev_demo"}],
        offers={
            77: {"id": 77, "name": "Alpha Offer"},
            88: {"id": 88, "name": "Beta Offer"},
        },
        streams_by_campaign=_base_streams(offer_entries=entries),
    )


@pytest.fixture
def api_client() -> TestClient:
    fake = _editor_fake()
    app_settings = _valid_settings()

    app.dependency_overrides[get_settings] = lambda: app_settings
    app.dependency_overrides[get_keitaro_client] = lambda: fake

    client = TestClient(app)
    try:
        yield client
    finally:
        app.dependency_overrides.clear()


def _offer_stream(body: list[dict[str, object]]) -> dict[str, object]:
    offer_streams = [item for item in body if item.get("name") == "offer"]
    assert len(offer_streams) == 1
    return offer_streams[0]


def test_get_streams_includes_geo_without_offer_rows(api_client: TestClient) -> None:
    response = api_client.get(f"/campaigns/{CAMPAIGN_ID}/streams")

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert len(body) == 2

    geo = next(item for item in body if item["name"] == "geo")
    assert geo["id"] == GEO_STREAM_ID
    assert "offers" not in geo

    offer = _offer_stream(body)
    assert offer["offers"] == [
        {"id": 77, "name": "Alpha Offer", "share": 100, "removed": False, "pinned": False},
    ]


def test_get_streams_returns_id_name_share_for_offer_stream(api_client: TestClient) -> None:
    fake = app.dependency_overrides[get_keitaro_client]()
    assert isinstance(fake, EditorFakeKeitaroClient)
    fake.streams_by_campaign = _base_streams(
        offer_entries=[
            {"offer_id": 77, "share": 50, "state": "active"},
            {"offer_id": 88, "share": 50, "state": "active"},
        ],
    )

    response = api_client.get(f"/campaigns/{CAMPAIGN_ID}/streams")

    assert response.status_code == 200
    offer = _offer_stream(response.json())
    assert offer["offers"] == [
        {"id": 77, "name": "Alpha Offer", "share": 50, "removed": False, "pinned": False},
        {"id": 88, "name": "Beta Offer", "share": 50, "removed": False, "pinned": False},
    ]


def test_get_streams_keeps_removed_offer_missing_from_keitaro(
    api_client: TestClient,
) -> None:
    fake = app.dependency_overrides[get_keitaro_client]()
    assert isinstance(fake, EditorFakeKeitaroClient)

    push_response = api_client.post(
        f"/campaigns/{CAMPAIGN_ID}/push",
        json={
            "offers": [
                {"id": 77, "removed": True, "pinned": False},
                {"id": 88, "removed": False, "pinned": False},
            ],
        },
    )
    assert push_response.status_code in {200, 204}

    fake.set_stream_offers(
        OFFER_STREAM_ID,
        [{"offer_id": 88, "share": 100, "state": "active"}],
    )

    response = api_client.get(f"/campaigns/{CAMPAIGN_ID}/streams")

    assert response.status_code == 200
    offer = _offer_stream(response.json())
    assert offer["offers"] == [
        {"id": 77, "name": "Alpha Offer", "share": 0, "removed": True, "pinned": False},
        {"id": 88, "name": "Beta Offer", "share": 100, "removed": False, "pinned": False},
    ]


def test_push_does_not_update_fake_until_called(api_client: TestClient) -> None:
    fake = app.dependency_overrides[get_keitaro_client]()
    assert isinstance(fake, EditorFakeKeitaroClient)
    fake.streams_by_campaign = _base_streams(
        offer_entries=[
            {"offer_id": 77, "share": 50, "state": "active"},
            {"offer_id": 88, "share": 50, "state": "active"},
        ],
    )

    response = api_client.get(f"/campaigns/{CAMPAIGN_ID}/streams")
    assert response.status_code == 200
    assert fake.updated_streams == []


def test_push_sends_shares_once_and_persists_removed_on_get(
    api_client: TestClient,
) -> None:
    fake = app.dependency_overrides[get_keitaro_client]()
    assert isinstance(fake, EditorFakeKeitaroClient)
    fake.streams_by_campaign = _base_streams(
        offer_entries=[
            {"offer_id": 77, "share": 50, "state": "active"},
            {"offer_id": 88, "share": 50, "state": "active"},
        ],
    )

    assert fake.updated_streams == []

    push_response = api_client.post(
        f"/campaigns/{CAMPAIGN_ID}/push",
        json={
            "offers": [
                {"id": 77, "removed": True, "pinned": False},
                {"id": 88, "removed": False, "pinned": False},
            ],
        },
    )
    assert push_response.status_code in {200, 204}

    assert len(fake.updated_streams) == 1
    pushed = fake.updated_streams[0]
    assert pushed["stream_id"] == OFFER_STREAM_ID
    assert pushed["offers"] == [
        {"offer_id": 77, "share": 0, "state": "active"},
        {"offer_id": 88, "share": 100, "state": "active"},
    ]

    after_push = api_client.get(f"/campaigns/{CAMPAIGN_ID}/streams")
    assert after_push.status_code == 200
    offer = _offer_stream(after_push.json())
    assert offer["offers"] == [
        {"id": 77, "name": "Alpha Offer", "share": 0, "removed": True, "pinned": False},
        {"id": 88, "name": "Beta Offer", "share": 100, "removed": False, "pinned": False},
    ]
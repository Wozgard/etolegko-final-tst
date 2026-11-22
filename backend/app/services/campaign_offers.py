from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.domain.weights import OfferShare, distribute_shares
from app.models.campaign_offer import CampaignOfferRow
from app.services.keitaro_client import KeitaroClient


def _find_offer_stream(streams: list[dict[str, Any]]) -> dict[str, Any] | None:
    for stream in streams:
        if "offers" in stream:
            return stream
    return None


def _keitaro_share_map(stream: dict[str, Any]) -> dict[int, int]:
    offers = stream.get("offers")
    if not isinstance(offers, list):
        return {}
    result: dict[int, int] = {}
    for entry in offers:
        offer_id = entry.get("offer_id")
        share = entry.get("share")
        if isinstance(offer_id, int) and isinstance(share, int):
            result[offer_id] = share
    return result


def _load_rows(db: Session, campaign_id: int) -> list[CampaignOfferRow]:
    return (
        db.query(CampaignOfferRow)
        .filter(CampaignOfferRow.campaign_id == campaign_id)
        .order_by(CampaignOfferRow.position)
        .all()
    )


def _offer_name(keitaro: KeitaroClient, offer_id: int) -> str:
    offer = keitaro.get_offer(offer_id)
    if offer and isinstance(offer.get("name"), str):
        return offer["name"]
    return str(offer_id)


def list_campaign_streams_response(
    keitaro: KeitaroClient,
    db: Session,
    campaign_id: int,
) -> list[dict[str, Any]]:
    streams = keitaro.list_campaign_streams(campaign_id)
    stored = _load_rows(db, campaign_id)
    result: list[dict[str, Any]] = []

    for stream in streams:
        if "offers" not in stream:
            result.append(dict(stream))
            continue

        keitaro_shares = _keitaro_share_map(stream)
        offer_rows: list[dict[str, Any]] = []

        if stored:
            for row in stored:
                share = keitaro_shares.get(row.offer_id, 0)
                offer_rows.append(
                    {
                        "id": row.offer_id,
                        "name": _offer_name(keitaro, row.offer_id),
                        "share": share,
                        "removed": row.removed,
                        "pinned": row.pinned,
                    }
                )
        else:
            raw_offers = stream.get("offers")
            if isinstance(raw_offers, list):
                for entry in raw_offers:
                    offer_id = entry.get("offer_id")
                    share = entry.get("share")
                    if not isinstance(offer_id, int) or not isinstance(share, int):
                        continue
                    offer_rows.append(
                        {
                            "id": offer_id,
                            "name": _offer_name(keitaro, offer_id),
                            "share": share,
                            "removed": False,
                            "pinned": False,
                        }
                    )

        stream_out = {key: value for key, value in stream.items() if key != "offers"}
        stream_out["offers"] = offer_rows
        result.append(stream_out)

    return result


def push_campaign_offers(
    keitaro: KeitaroClient,
    db: Session,
    campaign_id: int,
    offers: list[dict[str, Any]],
) -> None:
    streams = keitaro.list_campaign_streams(campaign_id)
    offer_stream = _find_offer_stream(streams)
    if offer_stream is None:
        raise ValueError("offer stream not found")

    stream_id = offer_stream.get("id")
    if not isinstance(stream_id, int):
        raise ValueError("offer stream id missing")

    current_shares = _keitaro_share_map(offer_stream)

    weight_inputs: list[OfferShare] = []
    for item in offers:
        offer_id = item["id"]
        removed = bool(item.get("removed", False))
        pinned = bool(item.get("pinned", False))
        if removed:
            share = 0
        elif pinned:
            requested = item.get("share")
            if isinstance(requested, int):
                share = requested
            else:
                share = current_shares.get(offer_id, 0)
        else:
            share = 0
        weight_inputs.append(OfferShare(str(offer_id), share, pinned, removed))

    distributed = distribute_shares(weight_inputs)

    db.query(CampaignOfferRow).filter(CampaignOfferRow.campaign_id == campaign_id).delete()
    for position, item in enumerate(offers):
        db.add(
            CampaignOfferRow(
                campaign_id=campaign_id,
                offer_id=item["id"],
                position=position,
                removed=bool(item.get("removed", False)),
                pinned=bool(item.get("pinned", False)),
            )
        )
    db.commit()

    keitaro_offers: list[dict[str, Any]] = []
    for index, weighted in enumerate(distributed):
        offer_id = offers[index]["id"]
        keitaro_offers.append(
            {
                "offer_id": offer_id,
                "share": weighted.share,
                "state": "active",
            }
        )

    keitaro.update_stream(stream_id, {"offers": keitaro_offers})
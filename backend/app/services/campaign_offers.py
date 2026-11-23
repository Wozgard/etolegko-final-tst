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


def _removed_response_share(row: CampaignOfferRow) -> int:
    if row.pinned and row.removed:
        return row.pinned_share
    return 0


def _pinned_share_from_item(
    item: dict[str, Any],
    *,
    removed: bool,
    pinned: bool,
    current_shares: dict[int, int],
) -> int:
    if not pinned:
        return 0
    requested = item.get("share")
    if isinstance(requested, int):
        return requested
    if not removed:
        offer_id = item["id"]
        return current_shares.get(offer_id, 0)
    return 0


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
            has_external_removal = False
            for row in stored:
                in_stream = row.offer_id in keitaro_shares
                if not in_stream and not row.removed:
                    has_external_removal = True
                if not in_stream:
                    share = _removed_response_share(row) if row.removed else 0
                    response_removed = True
                elif row.removed:
                    share = _removed_response_share(row)
                    response_removed = True
                else:
                    share = keitaro_shares[row.offer_id]
                    response_removed = False
                offer_rows.append(
                    {
                        "id": row.offer_id,
                        "name": _offer_name(keitaro, row.offer_id),
                        "share": share,
                        "removed": response_removed,
                        "pinned": row.pinned,
                    }
                )

            stored_ids = {row.offer_id for row in stored}
            for offer_id, share in keitaro_shares.items():
                if offer_id in stored_ids:
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

            if has_external_removal:
                previous_shares = [
                    {"id": entry["id"], "share": entry["share"]}
                    for entry in offer_rows
                ]
                weight_inputs = [
                    OfferShare(
                        str(entry["id"]),
                        entry["share"],
                        entry["pinned"],
                        entry["removed"],
                    )
                    for entry in offer_rows
                ]
                distributed = distribute_shares(weight_inputs)
                for index, weighted in enumerate(distributed):
                    entry = offer_rows[index]
                    if entry["removed"] and entry["pinned"]:
                        continue
                    offer_rows[index]["share"] = weighted.share
                stream_out = {
                    key: value for key, value in stream.items() if key != "offers"
                }
                stream_out["offers"] = offer_rows
                stream_out["external_change"] = {"previous_shares": previous_shares}
                result.append(stream_out)
                continue
        else:
            raw_offers = stream.get("offers")
            if isinstance(raw_offers, list):
                for position, entry in enumerate(raw_offers):
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
                    db.add(
                        CampaignOfferRow(
                            campaign_id=campaign_id,
                            offer_id=offer_id,
                            position=position,
                            removed=False,
                            pinned=False,
                            pinned_share=0,
                        )
                    )
                db.commit()

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
    pinned_shares: list[int] = []
    for item in offers:
        offer_id = item["id"]
        removed = bool(item.get("removed", False))
        pinned = bool(item.get("pinned", False))
        pinned_share = _pinned_share_from_item(
            item,
            removed=removed,
            pinned=pinned,
            current_shares=current_shares,
        )
        pinned_shares.append(pinned_share)
        if removed:
            share = 0
        elif pinned:
            share = pinned_share
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
                pinned_share=pinned_shares[position],
            )
        )
    db.commit()

    keitaro_offers: list[dict[str, Any]] = []
    for index, weighted in enumerate(distributed):
        if bool(offers[index].get("removed", False)):
            continue
        keitaro_offers.append(
            {
                "offer_id": offers[index]["id"],
                "share": weighted.share,
                "state": "active",
            }
        )

    keitaro.update_stream(stream_id, {"offers": keitaro_offers})
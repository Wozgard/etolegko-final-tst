from __future__ import annotations

import sys

import httpx


def main() -> int:
    base_url = "http://127.0.0.1:8000"
    with httpx.Client(timeout=30.0) as client:
        response = client.post(f"{base_url}/mock/remove-offers")
    if response.status_code == 404:
        print("Mock remove-offers endpoint is not available (keitaro_mock disabled).", file=sys.stderr)
        return 1
    response.raise_for_status()
    removed = response.json().get("removed", [])
    if not removed:
        print("В потоках их нет.")
        return 0
    by_campaign: dict[int, set[int]] = {}
    for entry in removed:
        campaign_id = entry["campaign_id"]
        offer_id = entry["offer_id"]
        by_campaign.setdefault(campaign_id, set()).add(offer_id)
    for campaign_id in sorted(by_campaign):
        offer_ids = ", ".join(str(offer_id) for offer_id in sorted(by_campaign[campaign_id]))
        print(f"Кампания {campaign_id}: сняты офферы {offer_ids}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
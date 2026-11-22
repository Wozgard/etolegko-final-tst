from dataclasses import dataclass


@dataclass
class OfferShare:
    id: str
    share: int
    pinned: bool = False
    removed: bool = False


def distribute_shares(offers: list[OfferShare]) -> list[OfferShare]:
    pinned_sum = sum(o.share for o in offers if o.pinned and not o.removed)
    if pinned_sum > 100:
        raise ValueError("sum of pinned shares exceeds 100")

    remainder = 100 - pinned_sum
    eligible = [i for i, o in enumerate(offers) if not o.removed and not o.pinned]

    distributed: dict[int, int] = {}
    if eligible:
        base, extra = divmod(remainder, len(eligible))
        for j, idx in enumerate(eligible):
            distributed[idx] = base + (1 if j < extra else 0)

    result: list[OfferShare] = []
    for i, o in enumerate(offers):
        if o.removed:
            share = 0
        elif o.pinned:
            share = o.share
        else:
            share = distributed.get(i, 0)
        result.append(OfferShare(o.id, share, o.pinned, o.removed))
    return result
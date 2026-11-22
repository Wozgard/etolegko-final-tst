import pytest

from app.domain.weights import OfferShare, distribute_shares


def _shares(result: list[OfferShare]) -> list[int]:
    return [o.share for o in result]


def test_empty_list() -> None:
    assert distribute_shares([]) == []


def test_single_active_offer_gets_100() -> None:
    offers = [OfferShare("a", 0)]
    assert _shares(distribute_shares(offers)) == [100]


def test_two_offers_split_50_50() -> None:
    offers = [
        OfferShare("a", 0),
        OfferShare("b", 0),
    ]
    assert _shares(distribute_shares(offers)) == [50, 50]


def test_three_offers_34_33_33() -> None:
    offers = [
        OfferShare("a", 0),
        OfferShare("b", 0),
        OfferShare("c", 0),
    ]
    assert _shares(distribute_shares(offers)) == [34, 33, 33]


def test_four_offers_25_each() -> None:
    offers = [OfferShare(f"o{i}", 0) for i in range(4)]
    assert _shares(distribute_shares(offers)) == [25, 25, 25, 25]


def test_seven_offers_remainder_spread_top_down() -> None:
    offers = [OfferShare(f"o{i}", 0) for i in range(7)]
    assert _shares(distribute_shares(offers)) == [15, 15, 14, 14, 14, 14, 14]


def test_pinned_77_four_free_6_6_6_5() -> None:
    offers = [
        OfferShare("pinned", 77, pinned=True),
        *[OfferShare(f"o{i}", 0) for i in range(4)],
    ]
    assert _shares(distribute_shares(offers)) == [77, 6, 6, 6, 5]


def test_pinned_50_two_others_25_25() -> None:
    offers = [
        OfferShare("pinned", 50, pinned=True),
        OfferShare("b", 50),
        OfferShare("c", 50),
    ]
    assert _shares(distribute_shares(offers)) == [50, 25, 25]


def test_removed_neighbor_zero_and_active_100() -> None:
    offers = [
        OfferShare("removed", 50, removed=True),
        OfferShare("active", 50),
    ]
    assert _shares(distribute_shares(offers)) == [0, 100]


def test_removed_pinned_does_not_reserve_weight() -> None:
    offers = [
        OfferShare("gone", 50, pinned=True, removed=True),
        OfferShare("active", 0),
    ]
    result = distribute_shares(offers)
    assert _shares(result) == [0, 100]
    assert result[0].pinned is True
    assert result[0].removed is True
    assert result[1].pinned is False
    assert result[1].removed is False


def test_pinned_33_two_others_33_34_33() -> None:
    offers = [
        OfferShare("pinned", 33, pinned=True),
        OfferShare("b", 0),
        OfferShare("c", 0),
    ]
    assert _shares(distribute_shares(offers)) == [33, 34, 33]


def test_pinned_sum_100_third_gets_zero() -> None:
    offers = [
        OfferShare("a", 60, pinned=True),
        OfferShare("b", 40, pinned=True),
        OfferShare("c", 25),
    ]
    assert _shares(distribute_shares(offers)) == [60, 40, 0]


def test_pinned_exceeds_100_raises() -> None:
    offers = [
        OfferShare("a", 70, pinned=True),
        OfferShare("b", 40, pinned=True),
    ]
    with pytest.raises(ValueError):
        distribute_shares(offers)


def test_all_removed_zeros() -> None:
    offers = [
        OfferShare("a", 50, removed=True),
        OfferShare("b", 50, removed=True),
    ]
    assert _shares(distribute_shares(offers)) == [0, 0]


def test_single_pinned_50_only() -> None:
    offers = [OfferShare("a", 50, pinned=True)]
    assert _shares(distribute_shares(offers)) == [50]


def test_preserves_order_and_length() -> None:
    offers = [
        OfferShare("z", 0),
        OfferShare("a", 0),
        OfferShare("m", 0),
    ]
    result = distribute_shares(offers)
    assert len(result) == len(offers)
    assert [o.id for o in result] == ["z", "a", "m"]


def test_does_not_mutate_input() -> None:
    offers = [
        OfferShare("a", 10, pinned=True),
        OfferShare("b", 20, removed=True),
        OfferShare("c", 30),
    ]
    before = [(o.id, o.share, o.pinned, o.removed) for o in offers]
    distribute_shares(offers)
    after = [(o.id, o.share, o.pinned, o.removed) for o in offers]
    assert before == after
import pages.common as common
from pages.common import resolve_slug, speech_tags_cte

ROWS = [
    (1, "Onions", "reviewed", None),
    (2, "Onion Prices", "merged", 1),
    (3, "Onion Price", "merged", 2),
    (4, "Lost", "merged", None),
    (5, "Bad Tag", "rejected", None),
    (6, "Same", "merged", 1),
    (7, "Same", "reviewed", None),
]


def test_resolve_slug_live_tag():
    assert resolve_slug(ROWS, "onions") == 1


def test_resolve_slug_merged_follows_chain():
    assert resolve_slug(ROWS, "onion-price") == 1
    assert resolve_slug(ROWS, "onion-prices") == 1


def test_resolve_slug_live_wins_over_merged():
    assert resolve_slug(ROWS, "same") == 7


def test_resolve_slug_unknown_rejected_or_dead_end():
    assert resolve_slug(ROWS, "nothing") is None
    assert resolve_slug(ROWS, "bad-tag") is None
    assert resolve_slug(ROWS, "lost") is None


def test_resolve_slug_loop_ends():
    loop = [(1, "A", "merged", 2), (2, "B", "merged", 1)]
    assert resolve_slug(loop, "a") is None


def test_resolve_slug_type_filter_skips_other_types():
    types = {1: "place", 7: "topic"}
    assert resolve_slug(ROWS, "onions", lambda i: types.get(i) == "place") == 1
    assert resolve_slug(ROWS, "same", lambda i: types.get(i) == "place") == 1


def test_speech_tags_cte_adds_one_condition():
    assert speech_tags_cte() == common.SPEECH_TAGS_CTE
    out = speech_tags_cte("si.speech_id = ANY(:ids)")
    assert "kt.id IS NOT NULL AND si.speech_id = ANY(:ids)" in out


def test_cached_keeps_value_until_ttl_ends(monkeypatch):
    calls = []
    common._cache.clear()
    assert common.cached("k", lambda: calls.append(1) or 5) == 5
    assert common.cached("k", lambda: calls.append(1) or 6) == 5
    assert len(calls) == 1
    monkeypatch.setattr(common, "CACHE_SECONDS", 0)
    assert common.cached("k", lambda: 7) == 7

from pages import speeches as S
from tests.pages_db import page_conn  # noqa: F401


def test_int_list_and_pairs():
    assert S.int_list("17, 18,x,19") == [17, 18, 19]
    assert S.int_list(None) == []
    assert S.session_pairs("17-15,18-1,bad,3") == [(17, 15), (18, 1)]
    assert S.int_arg("500", 20, 1, 50) == 50 and S.int_arg("x", 20, 1, 50) == 20 and S.int_arg("0", 20, 1, 50) == 1


def test_kind_types():
    types, other = S.kind_types(["zero_hour", "other", "nonsense"])
    assert "SPECIAL MENTION (ZERO HOUR)" in types and other
    assert S.kind_types(["nonsense"]) == ([], False)


def test_conditions_and_where_skip_own_filter():
    f = {"member": [1], "member_not": [], "tag_ids": [5], "place_ids": None, "subject": [], "term": [17], "session": [(17, 15)],
         "kind": [], "min_words": 0, "q": "", "party": ["BJP"], "party_not": []}
    c = S.conditions(f)
    assert set(c) == {"member", "tag", "term", "session", "party"}
    sql, params, party = S.where(c)
    assert party and "pa.party" in sql and params["term"] == [17]
    sql2, params2, party2 = S.where(c, S.OWN_FILTERS["party"])
    assert not party2 and "pa.party" not in sql2 and "party" not in params2
    assert S.where({})[0] == "true"


def test_make_excerpt():
    text = "First line here. So I went to Latur [r11] last week and saw Latur again.  Last one."
    ex, marks = S.make_excerpt(text, ["latur"])
    assert ex == "So I went to Latur last week and saw Latur again."
    assert [ex[a:b] for a, b in marks] == ["Latur", "Latur"]
    assert S.make_excerpt("Nothing here.", ["latur"]) == (None, [])
    assert S.make_excerpt("Latur-based plan", ["latur"])[1] == [[0, 5]]
    assert S.make_excerpt("Platurn is not it.", ["latur"]) == (None, [])
    long = "word " * 200 + "latur " + "word " * 200
    ex, marks = S.make_excerpt(long, ["latur"])
    assert len(ex) <= S.EXCERPT_CHARS and ex[marks[0][0]:marks[0][1]] == "latur"


def test_routes():
    assert ("/speeches", S.speeches_route) in S.ROUTES


def test_tag_total_equals_tag_page(page_conn):  # noqa: F811
    from pages.tag import tag_page
    out = S.speeches(page_conn, {"tag": "rural-employment"})
    assert out["total"] == tag_page(page_conn, "rural-employment", {})["total"]
    assert S.speeches(page_conn, {"tag": "no-such-tag-xyz"}) is None


def test_page_two_follows_page_one(page_conn):  # noqa: F811
    full = S.speeches(page_conn, {"tag": "rural-employment", "per_page": "50"})["speeches"]
    one = S.speeches(page_conn, {"tag": "rural-employment", "per_page": "20"})["speeches"]
    two = S.speeches(page_conn, {"tag": "rural-employment", "per_page": "20", "page": "2"})["speeches"]
    assert [r["id"] for r in one + two] == [r["id"] for r in full[:40]]


def test_word_search(page_conn):  # noqa: F811
    out = S.speeches(page_conn, {"q": "latur", "per_page": "50"})
    assert out["total"] == 109
    for r in out["speeches"]:
        assert r["excerpt"] and r["excerpt"][r["marks"][0][0]:r["marks"][0][1]].lower() == "latur"


def test_facets_add_up_and_skip_own_filter(page_conn):  # noqa: F811
    out = S.speeches(page_conn, {"facets": "1"})
    f = out["facets"]
    for k in ("term", "session", "kind"):
        assert sum(x["n"] for x in f[k]) == out["total"]
    narrowed = S.speeches(page_conn, {"facets": "1", "term": "17"})
    assert narrowed["total"] == next(x["n"] for x in f["term"] if x["term"] == 17)
    # the term facet ignores the term filter, so it equals the unfiltered term facet
    assert narrowed["facets"]["term"] == f["term"]
    assert sum(x["n"] for x in narrowed["facets"]["kind"]) == narrowed["total"]


def test_party_is_and_is_not(page_conn):  # noqa: F811
    args = {"tag": "rural-employment"}
    total = S.speeches(page_conn, args)["total"]
    a = S.speeches(page_conn, {**args, "party": "BJP"})["total"]
    b = S.speeches(page_conn, {**args, "party_not": "BJP"})["total"]
    known = sum(x["n"] for x in S.speeches(page_conn, {**args, "facets": "1"})["facets"]["party"])
    assert a + b == known <= total


def test_group_by_member_adds_up(page_conn):  # noqa: F811
    out = S.speeches(page_conn, {"tag": "rural-employment", "group": "member", "per_page": "50"})
    n = 0
    for p in range(1, out["pages"] + 1):
        n += sum(m["n"] for m in S.speeches(page_conn, {"tag": "rural-employment", "group": "member", "per_page": "50", "page": str(p)})["members"])
    assert n == out["total"]
    assert out["members"][0]["most_on"]


def test_unattributed_speeches_have_printed_name(page_conn):  # noqa: F811
    rows = S.speeches(page_conn, {"per_page": "50", "kind": "other"})["speeches"]
    nameless = [r for r in rows if not r["member"]]
    assert nameless and any(r["printed"] for r in nameless)  # some turns have an empty speaker label
    assert S.speeches(page_conn, {"tag": "rural-employment", "member_not": "219"})["total"] > 0


def test_csv(page_conn):  # noqa: F811
    resp = S.speeches(page_conn, {"member": "219", "format": "csv"})
    lines = resp.get_data(as_text=True).splitlines()
    assert resp.mimetype == "text/csv" and lines[0].startswith("date,term,session")
    assert len(lines) - 1 == S.speeches(page_conn, {"member": "219"})["total"]

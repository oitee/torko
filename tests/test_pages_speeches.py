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
         "kind": [], "min_words": 0, "q": "", "phrase": None, "party": ["BJP"], "party_not": []}
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


def test_group_by_member_with_party_filter(page_conn):  # noqa: F811
    # The count of members must join the party table when a party filter is on. It failed with a server error before.
    out = S.speeches(page_conn, {"q": "arrears", "party": "INC", "party_not": "BJP", "group": "member", "per_page": "50"})
    assert out["members_total"] == len(out["members"]) > 0
    assert all(m["party"] for m in out["members"])


def test_small_words_are_not_marked_unless_the_query_holds_nothing_else():
    from pages.speeches import highlight_words, make_excerpt
    assert highlight_words("farmers in Punjab") == ["farmers", "punjab"]
    assert highlight_words("in") == ["in"]
    excerpt, marks = make_excerpt("Farmers in Punjab protest.", highlight_words("farmers in Punjab"))
    assert [excerpt[a:b] for a, b in marks] == ["Farmers", "Punjab"]


def test_two_tags_need_one_speech_for_a_speech_and_any_speeches_for_a_member(page_conn):  # noqa: F811
    a, b = "farmers", "sugarcane"
    each = {t: {r["id"] for r in S.speeches(page_conn, {"tag": t, "per_page": "50"})["speeches"]} for t in (a, b)}
    assert all(each.values())
    both = S.speeches(page_conn, {"tag": f"{a},{b}", "per_page": "50"})
    alone = [S.speeches(page_conn, {"tag": t, "per_page": "1"})["total"] for t in (a, b)]
    assert 0 < both["total"] <= min(alone)
    members = S.speeches(page_conn, {"tag": f"{a},{b}", "group": "member", "per_page": "50"})
    assert members["members_total"] > 0
    for m in members["members"]:
        assert [t["slug"] for t in m["tag_counts"]] == [a, b]
        assert all(t["n"] > 0 for t in m["tag_counts"])


def test_an_unknown_tag_among_two_tags_gives_no_answer(page_conn):  # noqa: F811
    assert S.speeches(page_conn, {"tag": "farmers,no-such-tag-here"}) is None


def test_new_filters_build_their_conditions():
    base = {"member": [], "member_not": [], "tag_ids": None, "place_ids": None, "subject": [], "term": [], "session": [],
            "kind": [], "min_words": 0, "q": "", "phrase": None, "party": [], "party_not": []}
    c = S.conditions({**base, "term_not": [13], "session_not": [(17, 1)], "kind_not": ["zero_hour"], "tag_any_ids": [1], "tag_not_ids": [2],
                      "place_not_ids": [3], "subject_not": [4], "max_words": 9, "date_from": "2014-01-01", "date_to": "2015-01-01",
                      "title": "bill", "title_not": "x", "lang": ["hi"], "lang_not": ["en"], "state": ["Kerala"], "state_not": ["Goa"],
                      "seat": ["Kota"], "seat_not": ["Pali"]})
    assert {"term_not", "session_not", "kind_not", "tag_any", "tag_not", "place_not", "subject_not", "max_words", "date_from", "date_to",
            "title", "title_not", "lang", "lang_not", "state", "state_not", "seat", "seat_not"} == set(c)
    assert S.where({"state": c["state"]})[2] and S.where({"seat_not": c["seat_not"]})[2]
    assert not S.where({"lang": c["lang"]})[2]


def test_iso_date_and_like_pattern():
    assert S.iso_date("2014-05-26") == "2014-05-26"
    assert S.iso_date("2014-13-01") is None and S.iso_date("2014") is None and S.iso_date(None) is None
    assert S.like_pattern("50%_a") == "%50\\%\\_a%"


def test_real_filters_split_the_list(page_conn):
    term = S.speeches(page_conn, {"term": "17"})["total"]
    assert S.speeches(page_conn, {"term": "17", "kind": "zero_hour"})["total"] + S.speeches(page_conn, {"term": "17", "kind_not": "zero_hour"})["total"] == term
    a = S.speeches(page_conn, {"term": "17", "date_to": "2021-12-31"})["total"]
    b = S.speeches(page_conn, {"term": "17", "date_from": "2022-01-01"})["total"]
    assert a + b == term and a and b
    assert S.speeches(page_conn, {"term": "17", "min_words": "1000"})["total"] + S.speeches(page_conn, {"term": "17", "max_words": "999"})["total"] == term
    first = S.speeches(page_conn, {"term": "17", "tag": "farmers"})["total"]
    assert S.speeches(page_conn, {"term": "17", "tag_not": "farmers"})["total"] + first == term
    # Two tags: tag needs both, tag_any needs one, so tag_any holds at least as many as either tag.
    both = S.speeches(page_conn, {"tag": "farmers,union-budget"})["total"]
    either = S.speeches(page_conn, {"tag_any": "farmers,union-budget"})["total"]
    assert both < S.speeches(page_conn, {"tag": "farmers"})["total"] < either
    assert S.speeches(page_conn, {"tag_not": "no-such-tag-at-all"}) is None


def test_real_named_facets_and_names(page_conn):
    got = S.speeches(page_conn, {"term": "17", "state": "Kerala", "member": "392", "facets": "tag,state,seat,lang", "per_page": "1"})
    facets = got["facets"]
    assert {"tag", "state", "seat", "lang"} == set(facets) and "term" not in facets
    assert got["names"]["member"]["392"]
    only = S.speeches(page_conn, {"term": "17", "state": "Kerala", "facets": "state", "per_page": "1"})["facets"]["state"]
    assert len(only) > 1  # The state facet leaves out its own filter.
    assert S.speeches(page_conn, {"term": "17", "state": "Kerala"})["total"] == next(r["n"] for r in only if r["state"] == "Kerala")


def test_real_full_lists_for_the_pop_up(page_conn):
    got = S.speeches(page_conn, {"term": "17", "facets": "member,place,subject_all,tag_all", "per_page": "1"})["facets"]
    assert any("Tharoor" in r["name"] for r in got["member"])
    assert len(got["tag_all"]) > S.FACET_TAGS and got["place"] and got["subject_all"]
    assert got["member"][0]["n"] >= got["member"][-1]["n"]

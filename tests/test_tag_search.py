import tag_search
from tag_search import matches, search, words

TAGS = [{"tag": "Arrears", "aliases": [], "n_speeches": 10}, {"tag": "Tax Arrears", "aliases": [], "n_speeches": 1}]
SUBJECTS = [
    {"subject_id": "S1", "label": "Sugarcane farmers' arrears", "names": ["Sugarcane farmers' dues", "Sugarcane farmers arrears"],
     "parent_tag": "Arrears", "n_speeches": 46},
    {"subject_id": "S2", "label": "Wage arrears", "names": ["Wage arrears", "Employee salary arrears"],
     "parent_tag": "Arrears", "n_speeches": 7},
]


def test_words_drop_case_plurals_apostrophes_and_function_words():
    assert words("Farmers' Arrears of the State") == {"farmer", "arrear", "state"}


def test_a_text_matches_when_it_holds_every_query_word():
    assert matches("farmers arrears", "Sugarcane farmers' arrears")
    assert not matches("farmers arrears", "Wage arrears")


def test_a_broad_query_returns_the_tag_with_all_its_subjects_first():
    out = search("arrears", TAGS, SUBJECTS)
    assert out[0]["kind"] == "tag" and out[0]["name"] == "Arrears"
    assert [s["subject_id"] for s in out[0]["subjects"]] == ["S1", "S2"]
    assert all(r["kind"] != "subject" for r in out)


def test_a_specific_query_returns_the_subject_with_its_parent():
    out = search("farmers arrears", TAGS, SUBJECTS)
    assert [(r["kind"], r["subject_id"], r["parent_tag"]) for r in out] == [("subject", "S1", "Arrears")]


def test_a_query_that_misses_the_tag_name_still_finds_the_tag_through_its_subjects():
    tags = [{"tag": "Rural Employment Act (MNREGA)", "aliases": [], "n_speeches": 5}]
    subjects = [{"subject_id": "S1", "label": "MGNREGA wages", "names": ["MGNREGA wage dues"], "parent_tag": "Rural Employment Act (MNREGA)", "n_speeches": 9},
                {"subject_id": "S3", "label": "Employment guarantee funds", "names": ["MGNREGA funds"], "parent_tag": "Rural Employment Act (MNREGA)", "n_speeches": 3},
                {"subject_id": "S2", "label": "MGNREGA audit", "names": ["MGNREGA social audit"], "parent_tag": "", "n_speeches": 2}]
    out = search("MGNREGA", tags, subjects)
    assert out[0]["kind"] == "tag" and out[0]["name"] == "Rural Employment Act (MNREGA)"
    assert [r["subject_id"] for r in out[1:]] == ["S2"]


def test_the_search_endpoint_returns_the_tag_with_its_subjects(monkeypatch):
    import server
    monkeypatch.setattr(server, "_search_index", (TAGS, SUBJECTS, []))
    client = server.app.test_client()
    body = client.get("/api/search?q=arrears").get_json()
    assert body["results"][0]["name"] == "Arrears"
    assert [s["subject_id"] for s in body["results"][0]["subjects"]] == ["S1", "S2"]
    assert client.get("/api/search").status_code == 400


PLACES = [
    {"tag": "Aurangabad (Bihar)", "aliases": ["Aurangabad"], "n_speeches": 4, "type": "place",
     "description": "District and Lok Sabha constituency in Bihar, India."},
    {"tag": "Chhatrapati Sambhajinagar", "aliases": ["Aurangabad"], "n_speeches": 357, "type": "place",
     "description": "District and Lok Sabha constituency in Maharashtra, India."},
]
MEMBERS = [
    {"id": 1, "name": "A One", "seats": ["Aurangabad"], "seat": "Aurangabad", "state": "Bihar", "terms": [15], "n_speeches": 5},
    {"id": 2, "name": "B Two", "seats": ["Aurangabad"], "seat": "Aurangabad", "state": "Maharashtra", "terms": [17], "n_speeches": 50},
    {"id": 3, "name": "C Three", "seats": ["Delhi"], "seat": "Delhi", "state": "Delhi", "terms": [17], "n_speeches": 9},
]


def test_place_label_and_state_come_from_the_note():
    from tag_search import place_label, place_state
    assert place_state("District in Bihar, India.") == "Bihar"
    assert place_state("Major city in western India") is None
    assert place_label("Aurangabad (Bihar)", "District in Bihar, India.") == "Aurangabad, Bihar"
    assert place_label("Latur", "District and Lok Sabha constituency in Maharashtra, India.") == "Latur, Maharashtra"
    assert place_label("Delhi", None) == "Delhi"


def test_two_places_with_one_name_stay_two_results_with_their_own_state():
    out = search("aurangabad", PLACES, [], members=MEMBERS)
    places = [r for r in out if r["kind"] == "place"]
    assert sorted(r["state"] for r in places) == ["Bihar", "Maharashtra"]
    assert {r["slug"] for r in places} == {"aurangabad-bihar", "chhatrapati-sambhajinagar"}


def test_members_match_by_seat_and_show_their_own_state():
    out = search("aurangabad", PLACES, [], members=MEMBERS)
    members = [r for r in out if r["kind"] == "member"]
    assert [(m["id"], m["seat_label"]) for m in members] == [(2, "Aurangabad, Maharashtra"), (1, "Aurangabad, Bihar")]


def test_members_match_by_name_and_a_subject_has_its_parent_slug():
    out = search("three", [], [], members=MEMBERS)
    assert [r["id"] for r in out] == [3]
    subjects = [{"subject_id": "S", "label": "Wage arrears", "names": [], "parent_tag": "Tax Arrears", "n_speeches": 1}]
    assert search("wage", [], subjects)[0]["parent_tag_slug"] == "tax-arrears"


def test_a_tag_result_has_slug_type_and_domain():
    r = search("arrears", [{"tag": "Tax Arrears", "aliases": [], "n_speeches": 1, "type": "topic", "domain": "Economy"}], [])[0]
    assert (r["kind"], r["slug"], r["type"], r["domain"]) == ("tag", "tax-arrears", "topic", "Economy")


def test_a_tag_keeps_its_own_count_because_its_subjects_hold_the_same_speeches():
    # Farmers: the suggestion said 30,524 while the tag page said 15,225, because subject counts were added to the total.
    tags = [{"tag": "Farmers", "aliases": [], "n_speeches": 15225}]
    subjects = [{"subject_id": "S1", "label": "Farmers' income", "names": [], "parent_tag": "Farmers", "n_speeches": 9000},
                {"subject_id": "S2", "label": "Farmers' suicides", "names": [], "parent_tag": "Farmers", "n_speeches": 6299}]
    assert search("farmers", tags, subjects)[0]["n_speeches"] == 15225


def test_a_tag_found_through_its_subjects_keeps_its_own_count():
    tags = [{"tag": "Rural Employment Act (MNREGA)", "aliases": [], "n_speeches": 5}]
    subjects = [{"subject_id": "S1", "label": "MGNREGA wages", "names": [], "parent_tag": "Rural Employment Act (MNREGA)", "n_speeches": 4},
                {"subject_id": "S2", "label": "MGNREGA funds", "names": [], "parent_tag": "Rural Employment Act (MNREGA)", "n_speeches": 3}]
    assert search("MGNREGA", tags, subjects)[0]["n_speeches"] == 5


# named_pages: the cards above the search results.
NAMED_TAGS = [
    {"tag": "Raipur", "aliases": [], "n_speeches": 232, "type": "place", "description": "Raipur, a city in Chhattisgarh, India"},
    {"tag": "Raipur", "aliases": [], "n_speeches": 3, "type": "topic"},
    {"tag": "Corruption", "aliases": [], "n_speeches": 1302, "type": "topic"},
    {"tag": "Government", "aliases": [], "n_speeches": 59, "type": "topic"},
    {"tag": "Farmers", "aliases": [], "n_speeches": 17143, "type": "group"},
    {"tag": "Government of Kerala", "aliases": [], "n_speeches": 153, "type": "institution"},
    {"tag": "Kerala", "aliases": [], "n_speeches": 3926, "type": "place"},
    {"tag": "Aurangabad", "aliases": [], "n_speeches": 40, "type": "place"},
    {"tag": "Aurangabad", "aliases": [], "n_speeches": 30, "type": "place"},
    {"tag": "Empty", "aliases": [], "n_speeches": 0, "type": "topic"},
]


def named(q):
    return [(p["kind"], p["name"]) for p in tag_search.named_pages(q, NAMED_TAGS)]


def test_named_pages_gives_each_name_in_the_words_places_first_then_smaller_tags():
    assert named("raipur corruption") == [("place", "Raipur"), ("tag", "Corruption")]
    assert named("Raipur Corruption Government Farmers") == [("place", "Raipur"), ("tag", "Government"), ("tag", "Corruption")]


def test_named_pages_takes_the_longest_name_and_uses_its_words():
    assert named("government of kerala") == [("tag", "Government of Kerala")]


def test_named_pages_leaves_out_two_pages_with_one_name_and_tags_with_no_speeches():
    assert named("aurangabad") == []
    assert named("empty") == []
    assert named("of the in") == []


def test_named_pages_gives_the_link_fields_of_a_place():
    page = tag_search.named_pages("Raipur", NAMED_TAGS)[0]
    assert (page["kind"], page["slug"], page["n_speeches"]) == ("place", "raipur", 232)

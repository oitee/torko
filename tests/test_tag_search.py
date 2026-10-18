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
    monkeypatch.setattr(server, "_search_index", (TAGS, SUBJECTS))
    client = server.app.test_client()
    body = client.get("/api/search?q=arrears").get_json()
    assert body["results"][0]["name"] == "Arrears"
    assert [s["subject_id"] for s in body["results"][0]["subjects"]] == ["S1", "S2"]
    assert client.get("/api/search").status_code == 400

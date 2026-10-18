from scripts.subject_search import matches, search, words

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

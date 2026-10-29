"""The hand-checked content of the home page: each reference is checked against the database."""
import json

from pages.home_featured import FEATURED_FILE, contains, home_featured, load_featured, squash
from tests.pages_db import page_conn  # noqa: F401


def test_squash_ignores_case_and_runs_of_white_space():
    assert squash("  The MGNREGA,\n which  was ") == "the mgnrega, which was"


def test_contains_needs_the_whole_part_in_one_text():
    texts = ["Sir, the MGNREGA\nwas a demand-driven programme.", "Other turn."]
    assert contains(texts, "the mgnrega was a demand-driven")
    assert not contains(texts, "programme. Other turn.")
    assert not contains(texts, "")


def test_the_file_has_every_part():
    f = load_featured()
    assert {"member", "quote", "trend", "search_ideas"} <= set(f)


def test_the_real_file_passes_every_check(page_conn):
    out = home_featured(page_conn)
    assert out["omitted"] == []
    assert out["member"]["name"] and out["member"]["speeches"] > 0
    assert out["quote"]["member"] and out["quote"]["date"]
    assert out["trend"]["total"] > 0 and out["trend"]["years"]
    assert len(out["search_ideas"]) == len(load_featured()["search_ideas"])


def test_a_wrong_reference_is_left_out_and_named(page_conn, tmp_path):
    f = json.loads(FEATURED_FILE.read_text())
    f["quote"]["text"] = "A sentence that the member never said."
    f["member"]["member_id"] = f["member"]["member_id"] + 1
    f["trend"]["tag"] = "no-such-tag-anywhere"
    f["search_ideas"] = ["no-such-tag-anywhere"]
    path = tmp_path / "featured.json"
    path.write_text(json.dumps(f))
    out = home_featured(page_conn, path=path)
    assert out["quote"] is None and out["member"] is None and out["trend"] is None
    assert out["search_ideas"] == []
    assert len(out["omitted"]) == 4


def test_the_seat_is_the_seat_of_the_newest_term_that_has_one():
    from pages.home_featured import latest_seat
    rows = [(16, "Latur", "Maharashtra"), (18, None, None), (17, "Latur (SC)", "Maharashtra")]
    assert latest_seat(rows) == ("Latur (SC)", "Maharashtra")
    assert latest_seat([(18, None, None)]) == (None, None)
    assert latest_seat([]) == (None, None)


def test_each_quote_tag_gets_its_domain_and_its_subjects_one_time():
    from pages.home_featured import quote_tags
    tags = [{"name": "Arrears", "slug": "arrears", "type": "topic",
             "why": [{"subject": "Wage arrears of MGNREGA workers"}, {"subject": "Wage arrears of MGNREGA workers"},
                     {"subject": None}]},
            {"name": "Latur", "slug": "latur", "type": "place", "why": []}]
    assert quote_tags(tags, {"Arrears": "Labour and Employment"}) == [
        {"name": "Arrears", "slug": "arrears", "type": "topic", "domain": "Labour and Employment",
         "subjects": ["Wage arrears of MGNREGA workers"]},
        {"name": "Latur", "slug": "latur", "type": "place", "domain": None, "subjects": []}]


def test_the_real_member_has_a_seat_and_the_real_quote_has_tags(page_conn):
    out = home_featured(page_conn)
    assert out["member"]["seat"] and out["member"]["state"]
    assert out["quote"]["tags"] and all(t["slug"] for t in out["quote"]["tags"])

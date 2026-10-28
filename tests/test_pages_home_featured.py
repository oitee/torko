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

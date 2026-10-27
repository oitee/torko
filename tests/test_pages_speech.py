from pages.speech import clean_layout, group_reasons, speech_page, split_title
from tests.pages_db import page_conn  # noqa: F401


def test_clean_layout_removes_marks_only():
    assert clean_layout("a [r11] b (l1/1150 c") == "a b c"


def test_split_title_laid():
    assert split_title("Report  - Laid ") == ("Report", True)
    assert split_title("Report") == ("Report", False)


def test_group_reasons_attaches_items():
    tags = [{"name": "A", "source": "llm"}, {"name": "B", "source": "summary_tag"}]
    items = [{"tag": "A", "source": "llm", "mention": "x"}]
    out = group_reasons(tags, items)
    assert out[0]["why"] == [{"source": "llm", "mention": "x"}]
    assert out[1]["why"] == [] and out[1]["source_note"]


def test_speech_route(page_conn):
    r = speech_page(page_conn, 176660, {})
    assert r["id"] == 176660 and r["turn_list"]
    llm = [t for t in r["tags"] if t["source"] == "llm"]
    assert llm and all(t["why"] for t in r["tags"])
    assert any(w["mention"] for t in llm for w in t["why"])


def test_speech_unknown(page_conn):
    assert speech_page(page_conn, -5, {}) is None


def test_mention_places_offsets():
    from pages.speech import mention_places
    turns = [{"seq": 4, "own": True, "text": "Wages  rise. The wages fall."}, {"seq": 5, "own": False, "text": "wages"}]
    got = mention_places("wages", turns)
    assert got == [{"seq": 4, "start": 0, "end": 5}, {"seq": 4, "start": 17, "end": 22}]
    assert mention_places("", turns) == [] and mention_places("a  b", [{"seq": 1, "own": True, "text": "A b"}])


def test_marks_cover_the_mention(page_conn):
    r = speech_page(page_conn, 221881, {})
    by_seq = {t["seq"]: t["text"] for t in r["turn_list"]}
    n = 0
    for tg in r["tags"]:
        for w in tg["why"]:
            for m in w["marks"]:
                assert by_seq[m["seq"]][m["start"]:m["end"]].lower() == w["mention"].lower()
                n += 1
    assert n > 0
    assert all(w["marks"] == [] for tg in r["tags"] if tg["source"] == "summary_tag" for w in tg["why"])


def test_first_speech_of_debate_context(page_conn):
    r = speech_page(page_conn, 221881, {})
    assert r["earlier_speeches"] == 0 and r["later_speeches"] == r["debate_speeches"] - 1
    assert all(t["seq"] < r["turn_list"][0]["seq"] for t in r["before"])
    assert all(t["seq"] > r["turn_list"][-1]["seq"] for t in r["after"]) and len(r["after"]) <= 2


def test_subject_has_parent(page_conn):
    r = speech_page(page_conn, 221881, {})
    w = [w for tg in r["tags"] for w in tg["why"] if w["subject"]]
    assert w and w[0]["subject_id"] and w[0]["parent_tag"]["slug"]


def test_member_counts(page_conn):
    r = speech_page(page_conn, 218618, {})
    mc = r["member_counts"]
    assert mc["term_speeches"] >= mc["tag_speeches"] >= mc["tag_order"] >= 1
    # The oldest speech of the member on a tag has order 1.
    from sqlalchemy import text
    row = page_conn.execute(text("""
        SELECT x.id FROM speeches x JOIN debates d ON d.id = x.debate_id JOIN speech_items si ON si.speech_id = x.id AND si.kept
        WHERE x.person_id = :p AND si.tag_id = (SELECT id FROM tags WHERE tag = :t) ORDER BY d.debate_date, x.debate_id, x.seq_start LIMIT 1"""),
        {"p": r["member_id"], "t": mc["tag"]}).first()
    if row:
        assert speech_page(page_conn, row[0], {})["member_counts"]["tag_order"] == 1


def test_no_member_no_counts(page_conn):
    from sqlalchemy import text
    sid = page_conn.execute(text("SELECT id FROM speeches WHERE person_id IS NULL LIMIT 1")).scalar()
    assert speech_page(page_conn, sid, {})["member_counts"] is None

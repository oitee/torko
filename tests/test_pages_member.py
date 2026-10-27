import datetime as dt

import pages.member as m
from pages.common import speech_tags_cte
from tests.pages_db import page_conn  # noqa: F401


def test_split_name():
    assert m.split_name("Ravindra Shukla Alias Ravi Kishan") == ("Ravindra Shukla", "Ravi Kishan")
    assert m.split_name("N K Premachandran") == ("N K Premachandran", None)


def test_lift_is_share_over_share():
    assert m.lift(10, 100, 50, 1000) == 2.0


def test_pick_typical_rules():
    gtags = {
        1: {"tag": "Railways", "type": "topic", "n": 100},
        2: {"tag": "Kerala", "type": "place", "n": 80},
        3: {"tag": "Speaker", "type": "role", "n": 90},
        4: {"tag": "Rare", "type": "topic", "n": 5},
        5: {"tag": "Everything", "type": "topic", "n": 9000},
        6: {"tag": "Water", "type": "topic", "n": 100},
    }
    typical, places = m.pick_typical([(1, 5), (2, 7), (3, 9), (4, 9), (5, 9), (6, 2)], gtags, 10000, 50)
    assert [t["name"] for t in typical] == ["Railways"]
    assert [p["name"] for p in places] == ["Kerala"]
    assert typical[0]["lift"] == 10.0


def test_party_path_gives_years_in_date_order():
    d = dt.date
    rows = [(14, "SP", d(2004, 6, 2)), (15, "SP", d(2009, 6, 1)), (17, "BSP", d(2019, 6, 17)), (18, "SP", d(2024, 6, 24))]
    ends = {15: d(2014, 2, 1), 17: d(2024, 3, 1), 18: d(2026, 1, 1)}
    path = m.party_path(rows, ends, 18)
    assert path == [{"code": "SP", "from": 2004, "to": 2019}, {"code": "BSP", "from": 2019, "to": 2024},
                    {"code": "SP", "from": 2024, "to": None}]
    assert m.party_path([(15, "SP", d(2009, 6, 1))], ends, 18) == [{"code": "SP", "from": 2009, "to": 2014}]
    assert m.party_path([(15, None, d(2009, 6, 1))], ends, 18) == []


def test_median_with_zeros():
    assert m.median_with_zeros([5, 3], 5) == 0
    assert m.median_with_zeros([5, 3, 4], 4) == 3.5
    assert m.median_with_zeros([], 0) == 0


def test_shares():
    assert m.shares(10, 100, 50, 1000) == (0.1, 0.05, 2.0)
    assert m.shares(1, 0, 0, 0) == (0, 0, None)


def test_pick_seat_tag_uses_name_and_state():
    bihar = {"id": 1, "tag": "Aurangabad (Bihar)", "description": "District and Lok Sabha constituency in Bihar, India."}
    mah = {"id": 2, "tag": "Chhatrapati Sambhajinagar",
           "description": "District and Lok Sabha constituency in Maharashtra, India. The constituency is listed as Aurangabad."}
    assert m.pick_seat_tag("Aurangabad", "Bihar", [bihar, mah]) == 1
    assert m.pick_seat_tag("Aurangabad", "Maharashtra", [bihar, mah]) == 2
    assert m.pick_seat_tag("Aurangabad", None, [bihar, mah]) is None
    assert m.pick_seat_tag("Aurangabad", "Assam", [bihar, mah]) is None
    plain = {"id": 3, "tag": "Latur", "description": "District and Lok Sabha constituency in Maharashtra, India."}
    assert m.pick_seat_tag("Latur (SC)", "Maharashtra", [plain]) == 3
    assert m.pick_seat_tag("Latur", "Karnataka", [plain]) is None
    assert m.pick_seat_tag("Latur", None, [plain]) == 3


def test_restricted_cte_adds_condition():
    assert "AND si.speech_id = 1" in speech_tags_cte("si.speech_id = 1")


def test_member_page_real(page_conn):
    d = m.member_page(page_conn, "368", {})
    assert d["name"] == "Adhir Ranjan Chowdhury" and d["id"] == 368
    assert d["speeches"] > 1000 and 0 < d["tagged_speeches"] <= d["speeches"]
    assert d["typical"] and all(t["n"] <= t["all"] for t in d["typical"])
    assert len(d["marks"]) <= d["speeches"]
    assert d["recent"] and "counts_note" in d


def test_member_page_gives_the_state_of_each_seat(page_conn):
    d = m.member_page(page_conn, "368", {})
    assert d["seat"] == "Baharampur" and d["state"] == "West Bengal"
    assert all(t["state"] == "West Bengal" for t in d["terms"] if t["seat"])


def test_member_page_unknown(page_conn):
    assert m.member_page(page_conn, "99999999", {}) is None
    assert m.member_page(page_conn, "abc", {}) is None


def test_member_page_sessions_sum_and_median(page_conn):
    d = m.member_page(page_conn, "368", {})
    assert sum(x["n"] for x in d["sessions"]) == d["speeches"]
    assert all({"term", "session", "label", "n", "house_median"} <= set(x) for x in d["sessions"])
    one = [x for x in d["sessions"] if (x["term"], x["session"]) == (17, 5)][0]
    direct = page_conn.execute(m.text("""
        SELECT percentile_cont(0.5) WITHIN GROUP (ORDER BY n) FROM (
          SELECT (SELECT count(*) FROM speeches s JOIN debates d ON d.id = s.debate_id
                  WHERE s.person_id = p.person_id AND d.loksabha = 17 AND d.session = 5) AS n
          FROM (SELECT DISTINCT person_id FROM speakers WHERE lok_sabha_term = 17) p) x""")).scalar()
    assert one["house_median"] == direct


def test_member_page_party_path_of_a_changer(page_conn):
    d = m.member_page(page_conn, "66", {})
    assert [x["code"] for x in d["party_path"]] == ["SP", "BSP", "SP"]
    assert d["party_path"][1] == {"code": "BSP", "from": 2019, "to": 2024}
    assert d["party_path"][-1]["to"] is None


def test_member_page_aurangabad_seats_go_to_their_own_place(page_conn):
    assert m.member_page(page_conn, "1868", {})["seat_slug"] == "aurangabad-bihar"
    assert m.member_page(page_conn, "754", {})["seat_slug"] == "chhatrapati-sambhajinagar"
    own = [x for x in m.member_page(page_conn, "754", {})["places"] if x["own_seat"]]
    assert [x["slug"] for x in own] == ["chhatrapati-sambhajinagar"]


def test_member_page_house_share_over_member_terms(page_conn):
    d = m.member_page(page_conn, "754", {})
    row = d["typical"][0]
    terms = [t["term"] for t in d["terms"]]
    r = page_conn.execute(m.text(f"""
        WITH {m.SPEECH_TAGS_CTE}
        SELECT count(DISTINCT st.speech_id) FILTER (WHERE st.tag_id = :t), count(DISTINCT st.speech_id)
        FROM speech_tags st JOIN speeches s ON s.id = st.speech_id JOIN debates d ON d.id = s.debate_id
        WHERE d.loksabha = ANY(:terms)"""), {"t": row["tag_id"], "terms": terms}).one()
    assert row["house_share"] == round(r[0] / r[1], 4)
    assert row["member_share"] == round(row["n"] / d["tagged_speeches"], 4)
    assert "subjects" in row and d["other"]["n"] <= d["tagged_speeches"]


def test_pick_seat_tag_reads_the_state_anywhere_in_the_description():
    tags = [{"id": 1, "tag": "Thiruvananthapuram", "description": "Capital city of Kerala state."}]
    assert m.pick_seat_tag("Thiruvananthapuram", "Kerala", tags) == 1
    assert m.pick_seat_tag("Thiruvananthapuram", "Tamil Nadu", tags) is None

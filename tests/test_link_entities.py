import pytest
import json

from scripts.link_entities import (MODEL_ONLY, EXACT_MATCH, EXACT_VERSION, MAX_OPTIONS, NONE, Tags, decide_link, exact_tag,
                                   link_question, link_state, merge_candidates, needs_decision, norm_name, outcome,
                                   rule_report, split_by_rule, write_exact_link)


def test_norm_name_folds_case_spaces_and_outer_punctuation():
    assert norm_name("  The  MGNREGA. ") == "the mgnrega"
    assert norm_name("“Swachh Bharat”") == "swachh bharat"
    assert norm_name("Unlawful Activities (Prevention) Act") == "unlawful activities (prevention) act"


def test_norm_name_keeps_a_hindi_vowel_sign_at_the_end():
    assert norm_name("गंगा") == "गंगा"
    assert norm_name("गंगा।") == "गंगा"


def test_a_link_needs_a_tag_on_top_and_enough_probability():
    assert decide_link({"Water": 0.8, NONE: 0.2}) == ("linked", "Water", 0.8)
    assert decide_link({"Water": 0.65, NONE: 0.35}) == ("none", None, 0.65)
    assert decide_link({"Water": 0.3, NONE: 0.7}) == ("none", None, 0.7)
    assert decide_link({"Water": 0.65, NONE: 0.35}, link_p=0.6)[0] == "linked"


def test_exact_candidates_come_first_without_doubles_and_the_list_is_capped():
    vector = [(i, i / 100) for i in range(1, 30)]
    out = merge_candidates([5, 99], vector)
    assert [c["tag_id"] for c in out[:3]] == [5, 99, 1]
    assert out[0] == {"tag_id": 5, "source": "exact", "distance": 0.05}
    assert len(out) == MAX_OPTIONS and len({c["tag_id"] for c in out}) == MAX_OPTIONS


def test_the_question_always_offers_none():
    q = link_question("MGNREGA", "scheme", {"Rural Employment": "A law. Type: law."})
    assert set(q["criteria"]) == {"Rural Employment", NONE} and q["type"] == "choice"


def test_the_state_holds_the_examples():
    st = link_state("MGNREGA", "scheme", 12, [{"mention": "मनरेगा", "summary": "Asks for MGNREGA wages."}])
    assert "Type: scheme" in st and "12 speeches" in st and '"मनरेगा"' in st


def row(status, by="m q1", tsv=10):
    return {"link_status": status, "linked_by": by, "tag_set_version": tsv}


def test_a_link_stays_and_a_none_is_tried_again_when_new_tags_arrive():
    assert needs_decision(row("pending", None, None), "m q1", 10)
    assert not needs_decision(row("linked"), "m q1", 12)
    assert not needs_decision(row("none"), "m q1", 10)
    assert needs_decision(row("none"), "m q1", 12)
    assert needs_decision(row("linked", by="m q0"), "m q1", 10)
    assert needs_decision(row("linked"), "m q1", 10, force=True)


def test_the_four_gate_outcomes():
    assert outcome("Terrorism", ["Terrorism"]) == "correct link"
    assert outcome("Illegal Activities", ["Terrorism"]) == "wrong link"
    assert outcome(None, ["Terrorism"]) == "missed link"
    assert outcome(None, [NONE, "Criminal Law"]) == "correct none"
    assert outcome("Criminal Law", [NONE, "Criminal Law"]) == "correct link"


class Rows:
    def __init__(self, rows=None, scalar=None):
        self.rows, self.value = rows or [], scalar

    def all(self):
        return self.rows

    def scalar(self):
        return self.value


class FakeConn:
    def __init__(self, tag_rows):
        self.tag_rows, self.calls = tag_rows, []

    def execute(self, stmt, params=None):
        sql = str(stmt)
        if "FROM tags WHERE status" in sql:
            return Rows(self.tag_rows)
        if "max(id)" in sql:
            return Rows(scalar=max(r.id for r in self.tag_rows))
        self.calls.append((sql, params))
        return Rows()


class TagRow:
    def __init__(self, id, tag, type="topic", aliases=()):
        self.id, self.tag, self.type, self.description, self.aliases = id, tag, type, "d", list(aliases)


def tags_with(*rows):
    return Tags(FakeConn(list(rows)))


def name_row(norm, type="topic"):
    return {"id": 1, "norm_name": norm, "type": type, "name": norm}


def test_one_exact_tag_links_without_the_model():
    tags = tags_with(TagRow(1, "Water"), TagRow(2, "Rivers"))
    by_rule, rest = split_by_rule([name_row("water"), name_row("dams")], tags.exact)
    assert [r["norm_name"] for r in by_rule] == ["water"]
    assert [r["norm_name"] for r in rest] == ["dams"]
    assert exact_tag(tags.exact, "water") == 1


def test_two_distinct_exact_tags_go_to_the_model():
    tags = tags_with(TagRow(1, "Water"), TagRow(2, "Jal", aliases=["Water"]))
    assert exact_tag(tags.exact, "water") is None
    by_rule, rest = split_by_rule([name_row("water")], tags.exact)
    assert by_rule == [] and len(rest) == 1


def test_an_alias_match_counts_and_the_same_tag_twice_counts_once():
    tags = tags_with(TagRow(1, "Illegal Activities", aliases=["Unlawful Activities", "illegal activities"]))
    assert exact_tag(tags.exact, "unlawful activities") == 1
    assert exact_tag(tags.exact, "illegal activities") == 1


def test_a_rejected_tag_is_not_loaded_so_it_does_not_match():
    tags = tags_with(TagRow(1, "Water"))
    assert exact_tag(tags.exact, "rivers") is None


def test_the_tag_of_another_linked_name_is_not_a_tag_match():
    tags = tags_with(TagRow(1, "Water"))
    linked = {"jal": 1}
    assert exact_tag(tags.exact, "jal") is None
    assert split_by_rule([name_row("jal")], tags.exact)[0] == [] and "jal" in linked


def test_the_exact_link_is_written_with_the_reason_and_no_probability():
    tags = tags_with(TagRow(7, "Water"))
    conn = FakeConn([])
    write_exact_link(conn, name_row("water"), tags)
    sql, params = conn.calls[0]
    assert "link_p = NULL" in sql and "link_status = 'linked'" in sql
    assert params["tid"] == 7 and params["by"] == EXACT_VERSION and params["why"] == EXACT_MATCH
    assert json.loads(params["c"])[0]["source"] == "exact"


def linked_row(by, tag_id, status="linked", tsv=10):
    return {"link_status": status, "linked_by": by, "tag_set_version": tsv, "tag_id": tag_id}


def test_an_exact_link_stays_and_is_not_decided_again():
    assert not needs_decision(linked_row(EXACT_VERSION, 1), "m q1", 99, exact=1)


def test_an_exact_link_is_decided_again_when_the_exact_tag_changes_or_force_is_set():
    assert needs_decision(linked_row(EXACT_VERSION, 1), "m q1", 10, exact=2)
    assert needs_decision(linked_row(EXACT_VERSION, 1), "m q1", 10, force=True, exact=1)


def test_a_name_that_had_the_rule_and_now_has_two_exact_tags_goes_to_the_model():
    assert needs_decision(linked_row(EXACT_VERSION, 1), "m q1", 10, exact=None)


def test_a_model_decided_name_with_one_exact_tag_gets_the_rule():
    assert needs_decision(linked_row("m q1", 1), "m q1", 10, exact=1)
    assert needs_decision(linked_row("m q1", None, status="none"), "m q1", 10, exact=1)


def test_the_report_lists_exact_links_where_the_types_differ():
    tags = tags_with(TagRow(1, "Illegal Activities", "topic", ["Unlawful Activities"]), TagRow(2, "Water", "topic"))
    rows = [name_row("unlawful activities", "law"), name_row("water", "topic"), name_row("dams")]
    rep = rule_report(rows, tags)
    assert len(rep["one"]) == 2
    assert rep["mismatches"] == [("unlawful activities", "law", "Illegal Activities", "topic")]


def test_a_model_only_name_with_one_exact_tag_goes_to_the_model():
    tags = tags_with(TagRow(1, "Sagar", "place"), TagRow(2, "Water"))
    assert "sagar" in MODEL_ONLY
    assert exact_tag(tags.exact, "sagar") is None
    by_rule, rest = split_by_rule([name_row("sagar", "place")], tags.exact)
    assert by_rule == [] and len(rest) == 1
    assert tags.exact["sagar"] == [1]


def test_a_name_off_the_model_only_list_still_links_by_the_rule():
    tags = tags_with(TagRow(1, "Meerut", "place"))
    assert "meerut" not in MODEL_ONLY
    assert exact_tag(tags.exact, "meerut") == 1


def test_a_rule_link_on_a_model_only_name_is_decided_again_by_the_model():
    assert needs_decision(linked_row(EXACT_VERSION, 1), "m q1", 10, exact=exact_tag({"mandi": [1]}, "mandi"))


def test_the_report_counts_the_names_that_the_list_sent_to_the_model():
    tags = tags_with(TagRow(1, "Mandi", "place"), TagRow(2, "Meerut", "place"))
    rep = rule_report([name_row("mandi", "place"), name_row("meerut", "place")], tags)
    assert [r["norm_name"] for r in rep["model_only"]] == ["mandi"]
    assert [r["norm_name"] for r in rep["one"]] == ["meerut"]


def test_nearest_rows_orders_tags_by_cosine_distance_and_keeps_n():
    np = pytest.importorskip("numpy")
    from scripts.link_entities import nearest_rows
    tags = np.array([[1.0, 0.0], [0.0, 1.0], [0.6, 0.8]], dtype=np.float32)
    rows = nearest_rows([10, 20, 30], tags, [[2.0, 0.1], [0.0, 3.0]], n=2, chunk=1)
    assert [t for t, _ in rows[0]] == [10, 30]
    assert [t for t, _ in rows[1]] == [20, 30]
    assert rows[1][0][1] == pytest.approx(0.0, abs=1e-6)
    assert rows[1][1][1] == pytest.approx(0.2, abs=1e-6)


def test_only_these_keeps_listed_names_and_free_exact_links():
    from scripts.link_entities import only_these
    todo = [{"id": 1, "norm_name": "a"}, {"id": 2, "norm_name": "b"}, {"id": 3, "norm_name": "c"}]
    exact = {"c": [7], "b": [7, 8]}
    assert [r["id"] for r in only_these(todo, {1}, exact)] == [1, 3]

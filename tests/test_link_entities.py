from scripts.link_entities import (MAX_OPTIONS, NONE, decide_link, link_question, link_state, merge_candidates,
                                   needs_decision, norm_name, outcome)


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

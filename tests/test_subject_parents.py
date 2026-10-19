from collections import Counter

from scripts.subject_parents import (NONE, build_candidates, needs_decision, parent_question, parent_state,
                                     pick_examples)


def test_linked_tags_come_first_by_speeches_then_near_tags_that_are_new():
    cands = build_candidates(Counter({7: 3, 5: 10}), [(5, 0.2), (9, 0.25), (7, 0.3), (11, 0.31), (12, 0.4)],
                             max_linked=10, n_near=2)
    assert [(c["tag_id"], c["source"]) for c in cands] == [(5, "linked"), (7, "linked"), (9, "near"), (11, "near")]
    assert cands[0]["distance"] == 0.2


def test_a_subject_with_no_linked_name_gets_only_near_tags():
    cands = build_candidates(Counter(), [(1, 0.1), (2, 0.2), (3, 0.3), (4, 0.4)], n_near=3)
    assert [c["tag_id"] for c in cands] == [1, 2, 3]


def test_the_number_of_linked_tags_has_a_limit():
    cands = build_candidates(Counter({i: 100 - i for i in range(20)}), [], max_linked=10, n_near=3)
    assert len(cands) == 10 and cands[0]["tag_id"] == 0


def test_needs_decision():
    v = "jev p1"
    assert needs_decision(None, v, 10)
    assert needs_decision({"decided_by": "jev p0", "parent_tag_id": 3, "tag_set_version": 10}, v, 10)
    assert not needs_decision({"decided_by": v, "parent_tag_id": 3, "tag_set_version": 5}, v, 10)
    assert needs_decision({"decided_by": v, "parent_tag_id": None, "tag_set_version": 5}, v, 10)
    assert not needs_decision({"decided_by": v, "parent_tag_id": None, "tag_set_version": 10}, v, 10)
    assert needs_decision({"decided_by": v, "parent_tag_id": 3, "tag_set_version": 10}, v, 10, force=True)


def test_the_question_offers_none_and_says_a_narrower_tag_does_not_cover():
    q = parent_question("Religious tourism development", {"PRASAD Scheme": "A scheme. Type: scheme."})
    assert set(q["criteria"]) == {"PRASAD Scheme", NONE}
    assert "only one part of the subject does not cover it" in q["instructions"]


def test_the_state_lists_names_and_examples():
    names = [{"id": i, "name": f"n{i}", "n_speeches": 12 - i} for i in range(12)]
    s = parent_state("Wage arrears", names, 40, [{"mention": "wages are due", "summary": "The member asks."}])
    assert "Subject: Wage arrears" in s and "- n0 (12 speeches)" in s and "and 2 other names" in s
    assert "wages are due" in s


def test_examples_come_from_several_names_without_a_repeated_speech():
    names = [{"id": 1}, {"id": 2}]
    by_name = {1: [{"speech_id": 10}, {"speech_id": 11}], 2: [{"speech_id": 10}, {"speech_id": 12}]}
    assert [e["speech_id"] for e in pick_examples(names, by_name, 3)] == [10, 11, 12]

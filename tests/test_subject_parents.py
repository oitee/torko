from collections import Counter

from scripts.subject_parents import (NONE, NONE_TEXT, build_candidates, needs_decision, parent_question, parent_state,
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


def test_letters_go_past_z():
    from scripts.subject_parents import letters
    assert letters(28)[:2] == ["A", "B"] and letters(28)[25:] == ["Z", "AA", "AB"]


def test_only_a_high_answer_with_a_known_letter_gives_a_parent():
    from scripts.subject_parents import agent_decision
    codes = {"A": 5, "B": 9}
    assert agent_decision({"parent": "b", "confidence": "high"}, codes) == (9, 1.0, [])
    assert agent_decision({"parent": "B", "confidence": "low"}, codes) == (None, 0.5, [])
    assert agent_decision({"parent": "NONE", "confidence": "high"}, codes) == (None, 1.0, [])
    assert agent_decision({"parent": "C", "confidence": "high"}, codes)[0] is None
    assert agent_decision({"parent": "A", "confidence": "sure"}, codes)[0] is None


def test_the_job_block_lists_lettered_options_and_none():
    from scripts.subject_parents import job_block
    b = job_block("Subject: Wage arrears", "Wage arrears", [("A", "Arrears", "Money owed. Type: topic.")])
    assert "A. Arrears: Money owed. Type: topic." in b and b.endswith(f"NONE. {NONE_TEXT}")


def test_the_strict_rule_needs_one_linked_tag_that_is_also_nearest():
    from scripts.subject_parents import strict_rule
    near = lambda t, d: {"tag_id": t, "source": "near", "distance": d}
    linked = lambda t, d: {"tag_id": t, "source": "linked", "distance": d}
    assert strict_rule([linked(1, 0.2), near(2, 0.3)]) == 0
    assert strict_rule([linked(1, 0.2), near(2, 0.1)]) is None
    assert strict_rule([linked(1, 0.2), linked(3, 0.25), near(2, 0.3)]) is None
    assert strict_rule([linked(1, None), near(2, 0.3)]) is None
    assert strict_rule([near(2, 0.3)]) is None


def test_read_answers_adds_rule_answers_and_skips_unknown_ids(tmp_path):
    import json
    from scripts.subject_parents import read_answers
    (tmp_path / "out").mkdir()
    (tmp_path / "subjects.jsonl").write_text("\n".join(json.dumps({"subject": p, "key": k}) for p, k in
                                                       [("P00001", "1 2"), ("P00002", "3")]))
    (tmp_path / "out" / "j0001.out.jsonl").write_text('{"subject":"P00001","parent":"A","confidence":"high"}\nnot json\n'
                                                      '{"subject":"P09999","parent":"A","confidence":"high"}\n')
    (tmp_path / "rule.jsonl").write_text('{"subject":"P00002","parent":"B","confidence":"high","by":"rule"}\n')
    subs, answers = read_answers(tmp_path)
    assert set(answers) == {"P00001", "P00002"} and answers["P00002"]["by"] == "rule"


def test_agent_and_rule_answers_stay_and_jev_none_goes_to_the_agent():
    from scripts.subject_parents import needs_agent
    v = "jev p1"
    assert not needs_decision({"decided_by": "agent gemini-flash p1", "parent_tag_id": None, "tag_set_version": 1}, v, 10)
    assert not needs_decision({"decided_by": "rule linked+nearest p1", "parent_tag_id": 3, "tag_set_version": 1}, v, 10)
    assert needs_decision({"decided_by": "agent gemini-flash p1", "parent_tag_id": None, "tag_set_version": 1}, v, 10, force=True)
    assert needs_agent(None)
    assert needs_agent({"decided_by": v, "parent_tag_id": None})
    assert not needs_agent({"decided_by": v, "parent_tag_id": 3})
    assert not needs_agent({"decided_by": "agent gemini-flash p1", "parent_tag_id": None})

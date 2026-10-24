from types import SimpleNamespace

import pytest

from scripts.judge_items import (ROLES, USES, RunGuard, Thresholds, batches, gate_rates, judged_by, judgement, keep,
                                 p_keep, questions_for, read_item, read_marks, summary_state)


def subject(p, source="llm"):
    return {"subject_p": p, "use_p": None, "source": source}


def use(point, source="llm"):
    return {"subject_p": None, "use_p": {"absent": 0.0, "aside": 1 - point, "point": point, "other_meaning": 0.0},
            "source": source}


def test_an_llm_item_is_kept_at_a_low_limit():
    assert keep(subject(0.45)) and keep(use(0.45))
    assert not keep(subject(0.35)) and not keep(use(0.35))


def test_a_dictionary_entity_or_a_recognised_tag_is_kept_only_at_a_high_limit():
    for source in ("dictionary", "summary_tag"):
        assert not keep(use(0.75, source)) and not keep(subject(0.75, source))
        assert keep(use(0.85, source)) and keep(subject(0.85, source))


def test_the_limits_can_change():
    assert keep(subject(0.75, "summary_tag"), Thresholds(other=0.7))
    assert not keep(subject(0.45), Thresholds(llm=0.5))


def test_topics_and_recognised_tags_get_one_statement_and_named_items_get_one_use_question():
    q = questions_for([{"id": 7, "name": "Arbitration and Conciliation Act", "type": "law",
                        "mention": "Arbitration Act, 1996", "source": "llm"},
                       {"id": 9, "name": "Floods", "type": "topic", "mention": "बाढ़", "source": "llm"}])
    assert set(q) == {"use_7", "level_9"}
    assert q["level_9"] == {"type": "noul", "instructions":
                            "«Floods» (a topic) is a main or supporting subject of this speech, not only a passing mention."}
    assert q["use_7"]["type"] == "choice" and list(q["use_7"]["criteria"]) == list(USES)
    assert "«Arbitration Act, 1996»" in q["use_7"]["instructions"]


def test_a_recognised_tag_shows_its_type_and_no_description():
    tag = {"id": 7, "name": "Bareilly", "type": "place", "mention": "", "source": "summary_tag",
           "description": "District and Lok Sabha constituency in Uttar Pradesh, India."}
    q = questions_for([tag])
    assert list(q) == ["level_7"]
    assert "«Bareilly» (a place) is a main" in q["level_7"]["instructions"]
    assert "Uttar Pradesh" not in q["level_7"]["instructions"]


def test_a_dictionary_entity_gets_the_use_question_with_its_matched_words():
    q = questions_for([{"id": 8, "name": "DISHA", "type": "scheme", "mention": "दिशा", "source": "dictionary"}])
    assert list(q) == ["use_8"] and "«दिशा»" in q["use_8"]["instructions"]


def choice(probs):
    return {"type": "choice", "choice": max(probs, key=probs.get), "probabilities": probs}


def test_read_item_reads_a_named_item_by_its_use_and_keeps_the_source():
    answers = {"use_7": choice({"absent": 0.0, "aside": 0.1, "point": 0.85, "other_meaning": 0.05})}
    j, warnings, raw = read_item(answers, {"id": 7, "type": "law", "source": "dictionary"})
    assert j["use_p"]["point"] == 0.85 and j["source"] == "dictionary" and warnings == [] and set(raw) == {"use"}
    assert keep(j) and p_keep(j) == 0.85


def test_read_item_reads_a_topic_or_a_recognised_tag_by_one_probability():
    j, warnings, _ = read_item({"level_9": {"type": "noul", "noul": 0.7}}, {"id": 9, "type": "place",
                                                                           "source": "summary_tag"})
    assert j["subject_p"] == 0.7 and j["use_p"] is None and not warnings
    assert not keep(j)                                          # 0.7 is below the limit for additions


def test_read_item_warns_about_a_broken_sum():
    _, warnings, _ = read_item({"use_1": {"probabilities": {"point": 0.5}}}, {"id": 1, "type": "place"})
    assert warnings and "sum" in warnings[0]


def q4_row(source, level=None, role=None, refers=None):
    return SimpleNamespace(source=source, judge_subject_p=None, judge_use_p=None, judge_level_p=level,
                           judge_role_p=role, judge_refers_p=refers)


def test_a_row_that_q4_judged_is_read_with_the_limit_of_its_source():
    topic = judgement(q4_row("llm", level=[0.2, 0.35, 0.25, 0.2]))           # P(2+3) = 0.45
    assert keep(topic) and not keep({**topic, "source": "summary_tag"})
    assert ROLES == ("absent", "aside", "point")
    named = judgement(q4_row("dictionary", role=[0.0, 0.1, 0.9], refers=0.9))
    assert keep(named)
    assert not keep(judgement(q4_row("dictionary", role=[0.0, 0.1, 0.9], refers=0.5)))   # a guessed name


def test_a_row_that_q5_judged_is_read_from_its_own_columns():
    row = SimpleNamespace(source="llm", judge_subject_p=None, judge_use_p=[0.1, 0.2, 0.6, 0.1],
                          judge_level_p=None, judge_role_p=None, judge_refers_p=None)
    j = judgement(row)
    assert j["use_p"] == {"absent": 0.1, "aside": 0.2, "point": 0.6, "other_meaning": 0.1} and keep(j)


def test_summary_state_holds_the_summary_and_each_mention():
    s = {"member": "A", "title": "Floods", "debate_date": "2019-07-01"}
    st = summary_state(s, "Asks for flood relief.", [{"name": "Assam", "type": "place", "mention": "असम में बाढ़"}])
    assert "Asks for flood relief." in st and '"असम में बाढ़"' in st


def test_summary_state_marks_an_item_without_quoted_words():
    state = summary_state({"member": "M", "title": "T", "debate_date": "2019-07-01"}, "S.",
                          [{"name": "Railway Projects", "type": "topic", "mention": ""}])
    assert "- Railway Projects (topic): (no quoted words)" in state


def test_gate_rates_count_both_directions():
    r = gate_rates([(True, True), (True, False), (False, False), (False, True), (False, False)])
    assert r == {"manual_keep": 2, "model_keeps_of_those": 1, "manual_drop": 3, "model_drops_of_those": 2}


def test_version_names_model_and_questions():
    assert judged_by("jev-1.13.0") == "jev-1.13.0 q5"
    assert judged_by("jev-1.13.0", "q4") == "jev-1.13.0 q4"


def test_marks_are_read_from_a_review_column_and_from_an_old_owner_column(tmp_path):
    for column in ("review", "owner"):
        path = tmp_path / f"{column}.tsv"
        path.write_text(f"item_id\tname\t{column}\n1\ta\tKeep\n2\tb\tdrop\n3\tc\t\n4\td\tmaybe\n", encoding="utf-8")
        assert read_marks(path) == {1: True, 2: False}


def test_a_run_stops_after_failures_in_a_row_and_a_success_resets_the_count():
    g = RunGuard(max_failures=3)
    g.failure(); g.failure(); g.success(100); g.failure(); g.failure()
    assert g.reason is None
    g.failure()
    assert g.reason == "3 calls in a row failed"


def test_a_run_stops_when_its_tokens_reach_the_budget():
    g = RunGuard(max_tokens=10_000)
    g.success(6_000)
    assert g.reason is None and g.tokens == 6_000
    g.success(4_000)
    assert g.reason and "10,000" in g.reason


def test_a_run_with_no_budget_never_stops_on_tokens():
    g = RunGuard()
    g.success(10**12)
    assert g.reason is None


def test_batches_keep_every_id_once_in_order_and_the_last_batch_is_short():
    assert batches([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]]
    assert batches([1, 2, 3], 1000) == [[1, 2, 3]]
    assert batches([], 100) == []


def test_a_batch_size_below_one_is_refused():
    with pytest.raises(ValueError):
        batches([1, 2], 0)

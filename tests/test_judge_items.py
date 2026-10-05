"""Stage 4 must judge topics by centrality and named items by their role and their name, and never let the type decide."""
from scripts.judge_items import (LEVELS, ROLES, TYPES, Thresholds, gate_rates, judged_by, keep, questions_for,
                                 read_item, summary_state)


def named(point, refers, absent=0.0):
    return {"level_p": None, "role_p": {"absent": absent, "aside": 1 - point - absent, "point": point},
            "refers_p": refers}


def test_a_topic_is_kept_when_central_enough():
    assert keep({"level_p": [0.1, 0.2, 0.3, 0.4]})              # P(2+3) = 0.7
    assert not keep({"level_p": [0.2, 0.3, 0.3, 0.2]})          # P(2+3) = 0.5
    assert keep({"level_p": [0.2, 0.3, 0.3, 0.2]}, Thresholds(level=0.5))


def test_a_named_item_named_once_as_part_of_the_point_is_kept():
    assert keep(named(point=0.9, refers=0.9))


def test_an_example_or_a_courtesy_is_dropped_even_when_the_name_is_right():
    assert not keep(named(point=0.1, refers=0.95))


def test_a_guessed_full_name_is_dropped_even_when_part_of_the_point():
    assert not keep(named(point=0.9, refers=0.53))
    assert keep(named(point=0.9, refers=0.53), Thresholds(refers=0.5))


def test_topics_get_one_question_and_named_items_get_three():
    q = questions_for([{"id": 7, "name": "Arbitration and Conciliation Act", "type": "law",
                        "mention": "Arbitration Act, 1996"},
                       {"id": 9, "name": "Floods", "type": "topic", "mention": "बाढ़"}])
    assert set(q) == {"role_7", "refers_7", "type_7", "level_9"}
    assert q["level_9"]["criteria"] == LEVELS
    assert set(q["role_7"]["criteria"]) == set(ROLES) and set(q["type_7"]["criteria"]) == set(TYPES)
    assert "«Arbitration Act, 1996»" in q["refers_7"]["instructions"]
    assert "«Arbitration Act, 1996»" in q["role_7"]["instructions"]


def choice(probs):
    return {"type": "choice", "choice": max(probs, key=probs.get), "probabilities": probs}


def test_read_item_takes_its_own_answers_and_sets_the_type_only_when_sure():
    types = {t: 0.0 for t in TYPES}
    answers = {"role_7": choice({"absent": 0.0, "aside": 0.1, "point": 0.9}),
               "refers_7": {"type": "noul", "noul": 0.93},
               "type_7": choice({**types, "other": 0.8, "law": 0.2}),
               "role_8": choice({"absent": 0.0, "aside": 0.5, "point": 0.5}),
               "refers_8": {"type": "noul", "noul": 0.5},
               "type_8": choice({**types, "place": 0.6, "institution": 0.4})}
    j, warnings, raw = read_item(answers, {"id": 7, "type": "law"})
    assert j["role_p"]["point"] == 0.9 and j["refers_p"] == 0.93 and j["type"] == "other"
    assert warnings == [] and set(raw) == {"role", "refers", "type"}
    j, _, _ = read_item(answers, {"id": 8, "type": "place"})
    assert j["type"] is None                                   # 0.6 is below TYPE_P


def test_read_item_reads_a_topic_by_level_only():
    j, warnings, _ = read_item({"level_9": {"probabilities": {"0": 0.0, "1": 0.1, "2": 0.2, "3": 0.7}}},
                               {"id": 9, "type": "topic"})
    assert j["level_p"] == [0.0, 0.1, 0.2, 0.7] and j["role_p"] is None and warnings == []


def test_read_item_warns_about_a_broken_sum():
    _, warnings, _ = read_item({"level_1": {"probabilities": {"3": 0.5}}}, {"id": 1, "type": "topic"})
    assert warnings and "sum" in warnings[0]


def test_summary_state_holds_the_summary_and_each_mention():
    s = {"member": "A", "title": "Floods", "debate_date": "2019-07-01"}
    st = summary_state(s, "Asks for flood relief.", [{"name": "Assam", "type": "place", "mention": "असम में बाढ़"}])
    assert "Asks for flood relief." in st and '"असम में बाढ़"' in st


def test_gate_rates_count_both_directions():
    r = gate_rates([(True, True), (True, False), (False, False), (False, True), (False, False)])
    assert r == {"owner_keep": 2, "model_keeps_of_those": 1, "owner_drop": 3, "model_drops_of_those": 2}


def test_version_names_model_and_questions():
    assert judged_by("jev-1.13.0") == "jev-1.13.0 q3"

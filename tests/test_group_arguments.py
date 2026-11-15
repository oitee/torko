import scripts.group_arguments as ga


def test_a_list_with_the_join_call_records_both_prompts():
    assert ga.stored_version("group_v2", "merge_v1", True) == "group_v2+merge_v1"
    assert ga.stored_version("group_v2", "merge_v1", False) == "group_v2"


def test_a_short_list_gets_no_join_call(monkeypatch):
    calls = []

    def fake_ask(model, system, body, schema, check, key, tries, name):
        calls.append(system)
        return check({"groups": [{"label": "A", "points": [1]}, {"label": "B", "points": [2]}]})[0], [], {}

    monkeypatch.setattr(ga, "ask", fake_ask)
    item = {"id": "1-for", "input": "x", "n": 2, "order": [5, 6]}
    v = {"bill": "B", "year": 2020, "side": "for", "points": {5: "p", 6: "q"}}
    groups, problems, joins = ga.group_list("m", {"group": "G", "merge": "M"}, v, item, "k", 1)
    assert calls == ["G"] and joins is None and len(groups) == 2 and problems == []


def test_a_long_list_gets_the_join_call_and_a_refused_join_stores_nothing(monkeypatch):
    answers = {"G": {"groups": [{"label": f"L{i}", "points": [i]} for i in range(1, 6)]},
               "M": {"joins": [{"groups": [1, 1], "label": "X"}]}}

    def fake_ask(model, system, body, schema, check, key, tries, name):
        return (*check(answers[system]), {})

    monkeypatch.setattr(ga, "ask", fake_ask)
    item = {"id": "1-for", "input": "x", "n": 5, "order": [1, 2, 3, 4, 5]}
    v = {"bill": "B", "year": 2020, "side": "for", "points": {i: f"p{i}" for i in range(1, 6)}}
    groups, problems, _ = ga.group_list("m", {"group": "G", "merge": "M"}, v, item, "k", 1)
    assert groups == [] and problems
    answers["M"] = {"joins": [{"groups": [1, 2], "label": "X"}]}
    groups, problems, joins = ga.group_list("m", {"group": "G", "merge": "M"}, v, item, "k", 1)
    assert problems == [] and len(groups) == 4 and groups[0] == {"label": "X", "points": [1, 2]} and len(joins) == 1

import random

from scripts.extract_entities import MAX_OTHERS, MAX_TOPICS, SCHEMA, check_answer, pick, review_markdown


def item(name, salience=3, type_=None):
    e = {"name": name, "salience": salience, "mention": name.lower()}
    if type_:
        e["type"] = type_
    return e


def answer(topics=(), others=(), summary="Asks for flood relief in Assam.", language="en"):
    return {"language": language, "summary": summary, "topics": list(topics), "other_entities": list(others)}


def test_pick_is_the_same_for_the_same_seed_and_keeps_the_order():
    items = list(range(20))
    a, b = pick(items, 5, random.Random(1)), pick(items, 5, random.Random(1))
    assert a == b and a == sorted(a) and len(a) == 5


def test_pick_returns_everything_when_there_are_few_items():
    assert pick([3, 1], 5, random.Random(1)) == [3, 1]


def test_schema_caps_both_lists_and_keeps_topic_out_of_the_other_types():
    props = SCHEMA["properties"]
    assert props["topics"]["maxItems"] == MAX_TOPICS == 8
    assert props["other_entities"]["maxItems"] == MAX_OTHERS == 8
    assert "topic" not in props["other_entities"]["items"]["properties"]["type"]["enum"]
    assert "type" not in props["topics"]["items"]["properties"]


def test_a_clean_answer_passes_and_topics_get_the_type_topic():
    clean, warnings = check_answer(answer([item("Flood Relief", 5)], [item("Assam", 4, "place")]))
    assert warnings == []
    assert clean["topics"] == [{"name": "Flood Relief", "type": "topic", "salience": 5, "mention": "flood relief"}]
    assert clean["other_entities"][0]["type"] == "place"


def test_a_name_in_both_lists_stays_only_in_the_topics():
    clean, warnings = check_answer(answer([item("Farmers")], [item(" farmers ", 3, "group"), item("", 3, "place")]))
    assert [e["name"] for e in clean["topics"]] == ["Farmers"] and clean["other_entities"] == []
    assert len(warnings) == 2 and any("double item" in w for w in warnings)
    assert any("no name" in w for w in warnings)


def test_each_list_is_cut_to_eight_with_a_warning():
    clean, warnings = check_answer(answer([item(f"T{i}", 2) for i in range(10)],
                                          [item(f"P{i}", 2, "place") for i in range(9)]))
    assert len(clean["topics"]) == 8 and len(clean["other_entities"]) == 8
    assert sum("kept the first 8" in w for w in warnings) == 2


def test_missing_topics_and_too_many_fives_are_reported():
    _, warnings = check_answer(answer([], [item("Assam", 5, "place"), item("Bihar", 5, "place"), item("Goa", 5, "place")]))
    text = " ".join(warnings)
    assert "no topic" in text and "3 items at salience 5" in text


def test_bad_type_salience_language_and_long_summary_are_reported():
    _, warnings = check_answer(answer([item("X", 9)], [item("Y", 3, "topic")],
                                      summary=" ".join(["word"] * 31), language="fr"))
    text = " ".join(warnings)
    assert "unknown type 'topic'" in text and "salience out of range" in text
    assert "unknown language" in text and "31 words" in text


def test_review_file_has_two_tables_and_an_empty_review_line_per_speech():
    record = {"member": "A B", "title": " Floods\nin  Assam ", "debate_date": "2019-07-01", "loksabha": 17,
              "session": 1, "word_count": 300, "language": "en", "source_url": "https://x", "speech_id": 7,
              "excerpt": "text", "summary": "Asks for relief.", "warnings": [], "model": "m1", "prompt_version": "v1",
              "topics": [{"name": "Floods | Assam", "type": "topic", "salience": 5, "mention": "floods | assam"}],
              "other_entities": [{"name": "Assam", "type": "place", "salience": 3, "mention": "Asom",
                                  "mention_found": False}]}
    header = {"scope": "2019", "model": "m", "prompt": "p", "prompt_version": "v1", "run_date": "2026-10-03",
              "debates_sampled": 1, "debates_in_scope": 9, "per_debate": 3, "min_words": 100, "max_words": 5000, "seed": 1}
    md = review_markdown([record, {**record, "speech_id": 8, "topics": []}], header)
    assert md.count("\nreview: ") == 2
    assert "## 1. A B: Floods in Assam\n" in md and "version `v1`" in md
    assert "| Floods / Assam | floods / assam |" in md and md.count("(none)") == 1
    assert "| Asom *(not in text)* |" in md
    assert "model `m1`, prompt `v1`" in md


def test_an_existing_result_is_never_overwritten(tmp_path):
    from scripts.extract_entities import free_stem
    assert free_stem(tmp_path, "2019_seed1") == "2019_seed1"
    (tmp_path / "2019_seed1.md").write_text("reviewed")
    (tmp_path / "2019_seed1_2.jsonl").write_text("")
    assert free_stem(tmp_path, "2019_seed1") == "2019_seed1_3"


def test_plan_skips_done_speeches_and_holds_stale_ones_back_unless_asked():
    from scripts.extract_entities import plan
    existing = {1: "new", 2: "old"}
    assert plan([1, 2, 3], existing, "new", redo_stale=False) == ([3], [1], [2])
    assert plan([1, 2, 3], existing, "new", redo_stale=True) == ([3, 2], [1], [2])
    assert plan([1, 2], {1: "new", 2: "new"}, "new", redo_stale=True) == ([], [1, 2], [])


def test_force_extracts_again_every_speech_also_the_done_ones():
    from scripts.extract_entities import plan
    existing = {1: "new", 2: "old"}
    assert plan([1, 2, 3], existing, "new", redo_stale=False, force=True) == ([3, 2, 1], [1], [2])
    assert plan([1, 2, 3], existing, "new", redo_stale=True, force=True) == ([3, 2, 1], [1], [2])


def test_plan_never_counts_a_rule_stub_as_stale():
    from scripts.extract_entities import plan
    existing = {1: "new", 2: "old", 3: "old"}
    stubs = frozenset({3})
    assert plan([1, 2, 3, 4], existing, "new", redo_stale=True, stubs=stubs) == ([4, 2], [1, 3], [2])
    assert plan([3], existing, "new", redo_stale=True, stubs=stubs) == ([], [3], [])
    assert plan([3], existing, "new", redo_stale=True, force=True, stubs=stubs) == ([3], [3], [])


def test_mention_found_ignores_spaces_zero_width_characters_and_case():
    from scripts.extract_entities import mention_found
    speech = "रेल मंत्री जी, चाणस्‍मा से राधनपुर तक NEW Railway line"
    assert mention_found("चाणस् ‍ मा", speech)
    assert mention_found("new  railway", speech)
    assert not mention_found("Kutch", speech) and not mention_found("  ", speech)


def test_mention_checks_mark_each_item_and_warn_about_long_mentions():
    from scripts.extract_entities import add_mention_checks
    clean = {"topics": [{"name": "Rail", "mention": "railway line"}],
             "other_entities": [{"name": "Goa", "mention": "one two three four five six seven eight nine"}]}
    warnings = []
    add_mention_checks(clean, "a new railway line", warnings)
    assert clean["topics"][0]["mention_found"] and not clean["other_entities"][0]["mention_found"]
    assert len(warnings) == 1 and "9 words" in warnings[0]


def test_scope_filter_uses_the_term_or_the_year():
    from scripts.extract_entities import scope_filter
    assert scope_filter(None, 17) == ("d.loksabha = :term", {"term": 17})
    sql, params = scope_filter(2019, None)
    assert "make_date(:y, 1, 1)" in sql and params == {"y": 2019}


def test_estimate_counts_text_prompt_and_output_tokens():
    from scripts.extract_entities import estimate
    assert estimate(1000, 2) == {"input": 3500, "output": 940}


def test_prompt_versions_are_found_by_file_name_and_sorted_by_number(tmp_path):
    from scripts.extract_entities import prompt_versions
    for name in ("extract_v2.md", "extract_v10.md", "extract_v1.md", "extract_v1_draft.md", "notes.md"):
        (tmp_path / name).write_text("x")
    versions = prompt_versions(tmp_path)
    assert list(versions) == ["v1", "v2", "v10"]
    assert next(reversed(versions)) == "v10" and versions["v2"].name == "extract_v2.md"

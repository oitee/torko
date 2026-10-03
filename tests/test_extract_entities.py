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
              "excerpt": "text", "summary": "Asks for relief.", "warnings": [],
              "topics": [{"name": "Floods | Assam", "type": "topic", "salience": 5, "mention": "floods | assam"}],
              "other_entities": []}
    header = {"year": 2019, "model": "m", "prompt": "p", "prompt_md5": "0123456789abcdef", "run_date": "2026-10-03",
              "debates_sampled": 1, "debates_in_year": 9, "per_debate": 3, "min_words": 100, "max_words": 5000, "seed": 1}
    md = review_markdown([record, {**record, "speech_id": 8, "topics": []}], header)
    assert md.count("\nreview: ") == 2
    assert "## 1. A B: Floods in Assam\n" in md and "md5 `01234567`" in md
    assert "| Floods / Assam | floods / assam |" in md and md.count("(none)") == 3


def test_an_existing_result_is_never_overwritten(tmp_path):
    from scripts.extract_entities import free_stem
    assert free_stem(tmp_path, "2019_seed1") == "2019_seed1"
    (tmp_path / "2019_seed1.md").write_text("reviewed")
    (tmp_path / "2019_seed1_2.jsonl").write_text("")
    assert free_stem(tmp_path, "2019_seed1") == "2019_seed1_3"

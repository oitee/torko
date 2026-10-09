import csv

from scripts.build_entity_dictionary import COLUMNS, OFFICE_REASON, build, csv_row, has_office_word, load_exclusions, source_group, write_csv


def row(speech, name, mention, model="gemini-3.8-flash", type_="law", salience=3):
    return {"speech_id": speech, "model": model, "name": name, "type": type_, "salience": salience, "mention": mention}


def uses(name, mention, speeches, **kw):
    return [row(s, name, mention, **kw) for s in speeches]


def by_name(entries):
    return {e["name"]: e for e in entries}


def test_a_name_in_fewer_than_3_speeches_is_dropped_and_a_name_in_3_speeches_is_kept():
    rows = uses("Two", "two words", [1, 2]) + uses("Three", "three words", [1, 2, 3])
    entries, summary = build(rows)
    assert list(by_name(entries)) == ["Three"]
    assert summary["dropped_rule2"] == 2


def test_the_speech_count_uses_distinct_speeches_not_uses():
    rows = uses("Name", "name words", [1, 1, 1, 2])
    entries, summary = build(rows)
    assert entries == [] and summary["dropped_rule2"] == 4


def test_names_are_grouped_without_case_and_the_most_frequent_form_is_shown():
    rows = uses("Farmers", "kisan log", [1, 2]) + uses("farmers", "kisan log", [3]) + uses("Farmers", "kisan log", [4])
    entries, _ = build(rows)
    assert len(entries) == 1 and entries[0]["name"] == "Farmers" and entries[0]["speeches"] == 4
    assert "farmers (1)" in entries[0]["name_variants"]


def test_a_mention_used_once_is_dropped_and_a_mention_used_twice_is_kept():
    rows = uses("Name", "common phrase", [1, 2]) + uses("Name", "rare phrase", [3])
    entries, summary = build(rows)
    assert [m[0] for m in entries[0]["mentions"]] == ["common phrase"]
    assert summary["dropped_rule3"] == 1


def test_mentions_are_compared_without_case_and_spacing():
    rows = [row(1, "Name", "Big Phrase"), row(2, "Name", "big  phrase"), row(3, "Name", "bigphrase")]
    entries, _ = build(rows)
    assert len(entries[0]["mentions"]) == 1 and entries[0]["mentions"][0][1] == 3


def test_a_mention_of_3_characters_or_fewer_is_dropped():
    rows = uses("State", "UP", [1, 2, 3]) + uses("State", "Uttar", [1, 2, 3])
    entries, summary = build(rows)
    assert [m[0] for m in entries[0]["mentions"]] == ["Uttar"]
    assert summary["dropped_rule4"] == 3


def test_a_mention_of_4_characters_is_kept():
    entries, _ = build(uses("State", "Bihar", [1, 2, 3]) + uses("State", "Assam", [1, 2, 3]))
    assert len(entries[0]["mentions"]) == 2


def test_an_ambiguous_mention_is_dropped_and_listed_on_both_names():
    rows = (uses("Alpha", "shared word", [1, 2, 3]) + uses("Beta", "shared word", [4, 5, 6])
            + uses("Alpha", "alpha word", [1, 2, 3]) + uses("Beta", "beta word", [4, 5, 6]))
    entries, summary = build(rows)
    named = by_name(entries)
    assert [m[0] for m in named["Alpha"]["mentions"]] == ["alpha word"]
    assert named["Alpha"]["ambiguous_mentions"] == ["shared word (3)"]
    assert named["Beta"]["ambiguous_mentions"] == ["shared word (3)"]
    assert summary["dropped_rule5"] == 6


def test_a_mention_with_80_percent_for_one_name_is_not_ambiguous_and_goes_under_that_name():
    rows = uses("Alpha", "shared word", [1, 2, 3, 4, 5, 6, 7, 8]) + uses("Beta", "shared word", [9, 10])
    rows += uses("Beta", "other word", [9, 10, 11])
    entries, _ = build(rows)
    named = by_name(entries)
    assert named["Alpha"]["mentions"][0][:2] == ("shared word", 10)
    assert "Beta (2)" in named["Alpha"]["name_variants"]


def test_a_mention_with_79_percent_for_one_name_is_ambiguous():
    rows = uses("Alpha", "shared word", [1, 2, 3, 4]) + uses("Beta", "shared word", [5, 6, 7])
    rows += uses("Alpha", "alpha word", [1, 2, 3]) + uses("Beta", "beta word", [5, 6, 7])
    entries, summary = build(rows)
    assert summary["dropped_rule5"] == 7


def test_a_name_with_no_mention_left_is_not_in_the_dictionary():
    rows = uses("Gone", "UP", [1, 2, 3])
    entries, _ = build(rows)
    assert entries == []


def test_each_mention_counts_the_uses_by_strong_and_lite_models():
    rows = (uses("Name", "the phrase", [1, 2], model="gemini-3.8-flash") + uses("Name", "the phrase", [3, 4, 5], model="gemini-3.8-flash-lite")
            + uses("Name", "the phrase", [6], model="gemma-4-31b-it") + uses("Name", "only lite", [7, 8, 9], model="gemini-3.5-flash-lite"))
    e = build(rows)[0][0]
    assert ("the phrase", 6, 3, 3) in e["mentions"]
    r = csv_row(e)
    assert r["mentions_strong"] == "the phrase (3)"
    assert r["mentions_lite"] == "the phrase (3) | only lite (3)"
    assert r["mentions"] == "the phrase (6) | only lite (3)"


def test_the_source_group_of_a_model_follows_its_name():
    assert source_group("gemini-3.8-flash") == "strong"
    assert source_group("claude-sonnet-5-5") == "strong"
    assert source_group("gemini-3.5-flash-lite") == "lite"
    assert source_group("rule-stub") is None


def test_the_most_frequent_type_is_the_type_and_the_others_are_listed():
    rows = uses("Name", "some phrase", [1, 2, 3], type_="law") + uses("Name", "some phrase", [4], type_="scheme")
    e = build(rows)[0][0]
    assert e["type"] == "law" and e["other_types"] == ["scheme"]


def test_the_csv_has_the_documented_columns_and_can_be_read_back(tmp_path):
    entries, _ = build(uses("Name", "some phrase", [3, 1, 2]))
    path = tmp_path / "out.csv"
    write_csv(entries, path)
    rows = list(csv.DictReader(open(path, encoding="utf-8-sig")))
    assert list(rows[0]) == COLUMNS
    assert rows[0]["example_ids"] == "1 2 3" and rows[0]["n_mentions"] == "1"


def test_the_result_is_the_same_for_any_order_of_rows():
    rows = uses("A", "alpha word", [1, 2, 3]) + uses("B", "beta word", [4, 5, 6]) + uses("a", "alpha word", [7])
    assert build(rows)[0] == build(list(reversed(rows)))[0]


def test_names_that_differ_only_in_spaces_or_punctuation_become_one_entity():
    rows = (uses("Insolvency and Bankruptcy Code, 2016", "the code", [1, 2], ) + uses("Insolvency and Bankruptcy Code 2016", "the code", [3, 4])
            + uses("Insolvency and Bankruptcy Code, 2016", "ibc code", [5]))
    entries, summary = build(rows)
    assert len(entries) == 1 and entries[0]["speeches"] == 5
    assert entries[0]["name"] == "Insolvency and Bankruptcy Code, 2016"
    assert "Insolvency and Bankruptcy Code 2016 (2)" in entries[0]["name_variants"]
    assert summary["spelling_groups_merged"] == 1


def test_siddharthnagar_and_siddharth_nagar_merge_so_that_the_shared_mention_is_not_ambiguous():
    rows = (uses("Siddharthnagar", "सिद्धार्थनगर", range(1, 36)) + uses("Siddharth Nagar", "सिद्धार्थनगर", range(36, 44))
            + uses("Siddharthanagar", "सिद्धार्थनगर", [50]))
    entries, summary = build(rows)
    assert entries[0]["name"] == "Siddharthnagar" and entries[0]["mentions"][0][:2] == ("सिद्धार्थनगर", 43)
    assert summary["dropped_rule5"] == 0


def test_names_that_differ_in_a_digit_stay_separate_entities():
    rows = uses("Article 21", "article twenty one", [1, 2, 3]) + uses("Article 12", "article twelve", [4, 5, 6])
    entries, _ = build(rows)
    assert sorted(e["name"] for e in entries) == ["Article 12", "Article 21"]


def test_the_merge_happens_before_the_speech_count_so_that_two_spellings_can_reach_3_speeches():
    rows = uses("Rae Bareli", "rae bareli town", [1, 2]) + uses("Raebareli", "rae bareli town", [3])
    entries, _ = build(rows)
    assert len(entries) == 1 and entries[0]["speeches"] == 3


def test_an_excluded_name_is_dropped_whatever_its_spelling_and_the_count_goes_to_its_reason():
    import tempfile, pathlib
    path = pathlib.Path(tempfile.mkdtemp()) / "e.tsv"
    path.write_text("kind\tvalue\treason\nname\tLok Sabha\tbody\nmention\tthe chair\tprocedure\n", encoding="utf-8")
    ex = load_exclusions(path)
    rows = (uses("Lok sabha", "lok sabha house", [1, 2, 3]) + uses("LokSabha", "lok sabha house", [4])
            + uses("Dams", "the chair", [1, 2, 3]) + uses("Dams", "dam safety", [1, 2, 3]))
    entries, summary = build(rows, ex)
    assert [e["name"] for e in entries] == ["Dams"]
    assert [m[0] for m in entries[0]["mentions"]] == ["dam safety"]
    assert summary["excluded"] == {"body": 4, "procedure": 3}


def test_an_excluded_name_does_not_exclude_a_longer_name_that_contains_it():
    from entity_lookup import spelling_key
    ex = {"name": {spelling_key("India"): "country"}, "mention": {}}
    rows = uses("Air India", "air india", [1, 2, 3]) + uses("India", "india", [1, 2, 3])
    entries, _ = build(rows, ex)
    assert [e["name"] for e in entries] == ["Air India"]


def test_an_excluded_name_does_not_make_a_mention_ambiguous():
    from entity_lookup import spelling_key
    ex = {"name": {spelling_key("Parliament"): "body"}, "mention": {}}
    rows = uses("Parliament", "shared word", [1, 2, 3]) + uses("Bill", "shared word", [4, 5, 6])
    entries, summary = build(rows, ex)
    assert entries[0]["name"] == "Bill" and summary["dropped_rule5"] == 0


def test_a_person_mention_with_an_office_word_is_dropped_and_a_plain_name_is_kept():
    rows = (uses("Narendra Modi", "प्रधानमंत्री जी", [1, 2, 3], type_="person") + uses("Narendra Modi", "PM Modi", [1, 2, 3], type_="person")
            + uses("Narendra Modi", "Prime Minister Modi", [1, 2, 3], type_="person") + uses("Narendra Modi", "Narendra Modi", [1, 2, 3], type_="person")
            + uses("Narendra Modi", "मोदी जी", [1, 2, 3], type_="person"))
    entries, summary = build(rows)
    assert sorted(m[0] for m in entries[0]["mentions"]) == ["Narendra Modi", "मोदी जी"]
    assert summary["excluded"] == {OFFICE_REASON: 9}


def test_an_office_word_in_a_mention_of_a_non_person_is_kept():
    entries, _ = build(uses("Ministry of Railways", "Minister of Railways", [1, 2, 3], type_="institution"))
    assert len(entries) == 1


def test_an_office_word_must_be_a_whole_word():
    assert has_office_word("the Minister, Sir") and has_office_word("मुख्यमंत्री जी")
    assert not has_office_word("Ministerial Block") and not has_office_word("Pmo Delhi") and not has_office_word("Presidential")


def test_the_summary_counts_the_distinct_speeches_of_the_source():
    _, summary = build(uses("A", "alpha word", [1, 2, 3]) + uses("B", "beta word", [3, 4]))
    assert summary["source_speeches"] == 4


def test_the_real_exclusion_file_loads_and_has_the_three_columns_filled():
    from scripts.build_entity_dictionary import EXCLUDE_FILE
    ex = load_exclusions(EXCLUDE_FILE)
    assert ex["name"] and all(ex["name"].values())

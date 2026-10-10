from pathlib import Path

import pytest

from scripts.build_place_tags import (build, check, count_warnings, parse_constituencies, parse_districts,
                                      parse_old_constituencies, read_existing, read_tsv, tag_rows)
from scripts.link_entities import norm_name

DATA = Path(__file__).parent / "data"


def mini():
    districts, stated, _ = parse_districts((DATA / "places_districts_mini.html").read_text(encoding="utf-8"))
    constituencies, notes = parse_constituencies((DATA / "places_constituencies_mini.html").read_text(encoding="utf-8"))
    existing = read_existing(DATA / "places_existing_mini.tsv")
    renames = read_tsv(DATA / "places_renames_mini.tsv")
    return districts, stated, constituencies, notes, existing, renames


def tags_by_name(result):
    return {t["tag"]: t for t in result["tags"]}


def test_the_parser_strips_the_reservation_suffix_and_keeps_it_apart():
    _, _, constituencies, _, _, _ = mini()
    bihar = [c for c in constituencies if c["state"] == "Bihar"]
    assert [(c["name"], c["reserved"]) for c in bihar] == [("Aurangabad", "SC"), ("Gaya", "")]


def test_the_parser_skips_a_second_constituency_table_under_one_state():
    _, _, constituencies, notes, _, _ = mini()
    assert all(c["name"] != "Old Kerala Seat" for c in constituencies)
    assert any("second constituency table for Kerala" in n for n in notes)


def test_the_parser_removes_footnote_marks_from_district_names():
    districts, _, _, _, _, _ = mini()
    assert [d["name"] for d in districts if d["state"] == "Bihar"] == ["Aurangabad", "Gaya"]


def test_a_district_and_a_constituency_of_one_name_and_state_make_one_tag():
    districts, _, constituencies, _, existing, renames = mini()
    result = build(districts, constituencies, renames, existing)
    meerut = [t for t in result["tags"] if t["bare"] == "Meerut"]
    assert len(meerut) == 1
    assert meerut[0]["subtype"] == "district_constituency"
    assert meerut[0]["description"] == "District and Lok Sabha constituency in Uttar Pradesh, India."
    gaya = tags_by_name(result)["Gaya"]
    assert gaya["description"] == "District and Lok Sabha constituency in Bihar, India."


def test_a_name_in_two_states_gets_the_state_in_brackets_and_the_bare_alias():
    districts, _, constituencies, _, existing, renames = mini()
    tags = tags_by_name(build(districts, constituencies, renames, existing))
    assert "Hamirpur" not in tags
    assert tags["Hamirpur (Himachal Pradesh)"]["aliases"] == ["Hamirpur"]
    assert tags["Hamirpur (Uttar Pradesh)"]["aliases"] == ["Hamirpur"]


def test_the_bare_name_matches_two_tags_so_the_exact_rule_does_not_link_it():
    districts, _, constituencies, _, existing, renames = mini()
    result = build(districts, constituencies, renames, existing)
    owners = {}
    for t in result["tags"]:
        for n in [t["tag"], *t["aliases"]]:
            owners.setdefault(norm_name(n), set()).add(t["tag"])
    assert len(owners["hamirpur"]) == 2
    assert len(owners["meerut"]) == 1


def test_an_old_name_becomes_an_alias_and_the_constituency_joins_the_district():
    districts, _, constituencies, _, existing, renames = mini()
    tags = tags_by_name(build(districts, constituencies, renames, existing))
    prayagraj = tags["Prayagraj"]
    assert prayagraj["aliases"] == ["Allahabad"]
    assert prayagraj["subtype"] == "district_constituency"
    assert prayagraj["description"] == ("District and Lok Sabha constituency in Uttar Pradesh, India. "
                                        "The constituency is listed as Allahabad.")
    assert "Allahabad" not in tags


def test_a_renamed_district_and_a_same_named_district_in_another_state_share_the_bare_name():
    districts, _, constituencies, _, existing, renames = mini()
    result = build(districts, constituencies, renames, existing)
    tags = tags_by_name(result)
    assert tags["Chhatrapati Sambhajinagar"]["aliases"] == ["Aurangabad"]
    assert tags["Chhatrapati Sambhajinagar"]["subtype"] == "district_constituency"
    assert tags["Aurangabad (Bihar)"]["aliases"] == ["Aurangabad"]
    kinds = {(r["kind"], r["place"]) for r in result["review"]}
    assert ("shared_name", "Aurangabad (Bihar)") in kinds
    assert ("rename", "Chhatrapati Sambhajinagar") in kinds
    assert ("rename", "Prayagraj") in kinds


def test_a_place_with_an_existing_tag_name_gets_no_new_tag():
    districts, _, constituencies, _, existing, renames = mini()
    result = build(districts, constituencies, renames, existing)
    assert "Thiruvananthapuram" not in tags_by_name(result)
    rows = [r for r in result["review"] if r["kind"] == "existing_exact"]
    assert [(r["place"], r["other_tag"], r["other_type"], r["other_subtype"]) for r in rows] == [
        ("Thiruvananthapuram", "Thiruvananthapuram", "place", "city")]


def test_a_place_name_equal_to_a_tag_that_is_not_a_place_gets_no_tag_and_an_existing_exact_row():
    districts, _, constituencies, _, existing, renames = mini()
    existing[2]["alias_list"].append("Nashik")
    result = build(districts, constituencies, renames, existing)
    assert "Nashik" not in tags_by_name(result)
    rows = [r for r in result["review"] if r["kind"] == "existing_exact" and r["place"] == "Nashik"]
    assert [(r["other_tag"], r["other_type"]) for r in rows] == [("Plague", "topic")]


def test_a_name_on_the_hand_list_or_in_the_word_list_is_a_common_word_row():
    districts, _, constituencies, _, existing, renames = mini()
    result = build(districts, constituencies, renames, existing, common_words=[{"word": "Gaya", "meaning": "test"}],
                   word_list={"nashik"})
    rows = {(r["place"], r["detail"].split(":")[0]) for r in result["review"] if r["kind"] == "common_word"}
    assert rows == {("Gaya", "method hand_list"), ("Nashik", "method english_word")}


def test_a_diacritic_gives_an_ascii_alias_and_the_alias_is_dropped_when_it_is_taken():
    districts = [{"name": "Mahé", "state": "Puducherry", "source_row": "t #1"}]
    result = build(districts, [], [], [])
    assert result["tags"][0]["aliases"] == ["Mahe"]


def test_the_output_has_the_columns_of_the_seed_file():
    districts, _, constituencies, _, existing, renames = mini()
    rows = tag_rows(build(districts, constituencies, renames, existing)["tags"])
    assert list(rows[0]) == ["tag", "type", "subtype", "domain", "description", "aliases", "debate_count"]
    assert rows[0]["type"] == "place" and rows[0]["domain"] == "-" and rows[0]["debate_count"] == 0


def test_the_self_check_passes_on_good_data_and_reports_the_543_rule():
    districts, stated, constituencies, _, existing, renames = mini()
    result = build(districts, constituencies, renames, existing)
    faults = check(result, constituencies, districts, stated, existing)
    assert faults == [f"{len(constituencies)} constituency rows, expected 543"]
    assert count_warnings(districts, stated) == []


def test_the_self_check_finds_an_alias_that_equals_another_new_tag():
    districts, stated, constituencies, _, existing, renames = mini()
    result = build(districts, constituencies, renames, existing)
    tags = tags_by_name(result)
    tags["Gaya"]["aliases"].append("Meerut")
    faults = check(result, constituencies, districts, stated, existing)
    assert any("alias 'Meerut' of 'Gaya' equals the name of the new tag 'Meerut'" in f for f in faults)


KUTCH_D = [{"name": "Kutch", "state": "Gujarat", "source_row": "d #1"}]
KUTCH_C = [{"name": "Kachchh", "state": "Gujarat", "reserved": "", "source_row": "c #1"}]
KUTCH_SAME = [{"name_a": "Kutch", "name_b": "Kachchh", "state": "Gujarat", "keep": "Kutch", "note": ""}]


def test_two_spellings_of_one_place_in_same_place_make_one_tag_with_the_other_spelling_as_alias():
    result = build(KUTCH_D, KUTCH_C, [], [], same_place=KUTCH_SAME)
    assert [t["tag"] for t in result["tags"]] == ["Kutch"]
    tag = result["tags"][0]
    assert tag["subtype"] == "district_constituency" and tag["aliases"] == ["Kachchh"]
    assert tag["description"] == ("District and Lok Sabha constituency in Gujarat, India. "
                                  "The constituency is listed as Kachchh.")
    assert tag["sources"] == ["d #1", "c #1"]
    assert result["log"]["merged"] == ["Gujarat: Kutch (kept) and Kachchh are one place"]


def test_without_a_same_place_row_the_two_spellings_stay_two_tags():
    result = build(KUTCH_D, KUTCH_C, [], [])
    assert sorted(t["tag"] for t in result["tags"]) == ["Kachchh", "Kutch"]


def test_a_same_place_row_with_a_missing_name_or_two_places_of_one_kind_is_an_error():
    with pytest.raises(ValueError):
        build(KUTCH_D, KUTCH_C, [], [], same_place=[{**KUTCH_SAME[0], "name_b": "Nowhere"}])
    two_districts = KUTCH_D + [{"name": "Kachchh", "state": "Gujarat", "source_row": "d #2"}]
    with pytest.raises(ValueError):
        build(two_districts, [], [], [], same_place=KUTCH_SAME)


def test_the_name_a_merged_tag_gets_is_the_keep_name_even_when_it_is_the_second_name():
    rows = [{**KUTCH_SAME[0], "keep": "Kachchh"}]
    result = build(KUTCH_D, KUTCH_C, [], [], same_place=rows)
    assert result["tags"][0]["tag"] == "Kachchh" and result["tags"][0]["aliases"] == ["Kutch"]


def test_an_extra_alias_is_added_and_an_unknown_tag_is_an_error():
    districts = [{"name": "Maldah", "state": "West Bengal", "source_row": "d #1"}]
    result = build(districts, [], [], [], extra_aliases=[{"alias": "Malda", "tag": "Maldah"}])
    assert result["tags"][0]["aliases"] == ["Malda"] and result["log"]["extra_aliases"] == 1
    with pytest.raises(ValueError):
        build(districts, [], [], [], extra_aliases=[{"alias": "Malda", "tag": "Nowhere"}])


def test_the_self_check_finds_an_extra_alias_that_equals_another_tag_or_an_existing_tag():
    districts = [{"name": "Maldah", "state": "West Bengal", "source_row": "d #1"},
                 {"name": "Nadia", "state": "West Bengal", "source_row": "d #2"}]
    result = build(districts, [], [], [], extra_aliases=[{"alias": "Nadia", "tag": "Maldah"}])
    faults = check(result, [], districts, {}, [])
    assert any("alias 'Nadia' of 'Maldah' equals the name of the new tag 'Nadia'" in f for f in faults)
    existing = [{"tag": "Malda Town", "type": "place", "subtype": "city", "aliases": "Malda", "alias_list": ["Malda"]}]
    result = build(districts, [], [], existing, extra_aliases=[{"alias": "Malda", "tag": "Maldah"}])
    assert any("alias 'Malda' of 'Maldah' equals an existing tag" in f for f in check(result, [], districts, {}, existing))


def test_the_parser_returns_the_rows_of_the_second_table_under_a_state():
    html = (DATA / "places_constituencies_mini.html").read_text(encoding="utf-8")
    assert [(r["name"], r["state"]) for r in parse_old_constituencies(html)] == [("Old Kerala Seat", "Kerala")]


OLD = [{"name": "Gauhati", "state": "Assam", "reserved": "", "source_row": "o #1"},
       {"name": "Mangaldoi", "state": "Assam", "reserved": "", "source_row": "o #2"},
       {"name": "Silchar", "state": "Assam", "reserved": "", "source_row": "o #3"},
       {"name": "Typo", "state": "Assam", "reserved": "", "source_row": "o #4"}]
OLD_DECISIONS = [{"old_name": "Gauhati", "state": "Assam", "decision": "alias", "target": "Guwahati", "note": ""},
                 {"old_name": "Mangaldoi", "state": "Assam", "decision": "former", "target": "", "note": ""},
                 {"old_name": "Silchar", "state": "Assam", "decision": "same", "target": "", "note": ""},
                 {"old_name": "Typo", "state": "Assam", "decision": "ignore", "target": "", "note": ""}]
CURRENT = [{"name": "Guwahati", "state": "Assam", "reserved": "", "source_row": "c #1"},
           {"name": "Silchar", "state": "Assam", "reserved": "SC", "source_row": "c #2"}]


def test_each_old_seat_is_an_alias_a_former_tag_or_nothing_by_its_decision():
    result = build([], CURRENT, [], [], old_seats=OLD, old_decisions=OLD_DECISIONS)
    tags = tags_by_name(result)
    assert sorted(tags) == ["Guwahati", "Mangaldoi", "Silchar"]
    assert tags["Guwahati"]["aliases"] == ["Gauhati"]
    assert tags["Mangaldoi"]["subtype"] == "former_constituency"
    assert tags["Mangaldoi"]["description"] == "Former Lok Sabha constituency in Assam, India (until 2024)."
    assert tags["Silchar"]["aliases"] == []


def test_a_former_tag_can_get_another_name_than_the_old_name():
    decisions = [{**OLD_DECISIONS[1], "target": "Mangaldoi (Assam)"}] + OLD_DECISIONS[:1] + OLD_DECISIONS[2:]
    tags = tags_by_name(build([], CURRENT, [], [], old_seats=OLD, old_decisions=decisions))
    assert "Mangaldoi (Assam)" in tags and "Mangaldoi" not in tags


def test_a_former_tag_takes_the_hand_made_description_when_one_is_given():
    text = "Town in the Darrang district of Assam, India. A Lok Sabha constituency until 2024."
    decisions = [{**OLD_DECISIONS[1], "description": text}] + OLD_DECISIONS[:1] + OLD_DECISIONS[2:]
    tags = tags_by_name(build([], CURRENT, [], [], old_seats=OLD, old_decisions=decisions))
    assert tags["Mangaldoi"]["description"] == text


def test_an_old_seat_without_a_decision_or_a_wrong_decision_is_an_error():
    with pytest.raises(ValueError):
        build([], CURRENT, [], [], old_seats=OLD, old_decisions=OLD_DECISIONS[:3])
    with pytest.raises(ValueError):
        build([], CURRENT, [], [], old_seats=OLD[:3], old_decisions=[{**OLD_DECISIONS[2], "old_name": "Silchar", "decision": "same"},
                                                                      {**OLD_DECISIONS[0], "target": "Nowhere"}, OLD_DECISIONS[1]])
    bad_same = [{**OLD_DECISIONS[1], "decision": "same"}] + OLD_DECISIONS[:1] + OLD_DECISIONS[2:]
    with pytest.raises(ValueError):
        build([], CURRENT, [], [], old_seats=OLD, old_decisions=bad_same)

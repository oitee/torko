from scripts.load_tags import SOURCES, plan_load


def row(tag, aliases=(), desc="d", typ="place"):
    return {"tag": tag, "type": typ, "subtype": None, "domain": None, "description": desc,
            "aliases": list(aliases), "debate_count": 0}


def stored(tag, source, **kw):
    return {**row(tag, **kw), "source": source}


def test_two_sources_load_new_tags_into_their_own_source():
    files = {"seed_v1": [row("Roads", typ="topic")], "places_v1": [row("Pune")]}
    plan = plan_load(files, [], {"seed_v1", "places_v1"})
    assert [r["tag"] for r in plan["sources"]["seed_v1"]["insert"]] == ["Roads"]
    assert [r["tag"] for r in plan["sources"]["places_v1"]["insert"]] == ["Pune"]
    assert plan["errors"] == []


def test_same_name_in_two_lists_is_an_error_with_the_same_normal_form():
    files = {"seed_v1": [row("Pune")], "places_v1": [row("  pune. ")]}
    plan = plan_load(files, [], {"seed_v1", "places_v1"})
    assert len(plan["errors"]) == 1 and "same name" in plan["errors"][0]


def test_name_equal_to_alias_in_other_list_is_a_warning_only():
    files = {"seed_v1": [row("Bombay", aliases=["Mumbai City"])], "places_v1": [row("Mumbai City")]}
    plan = plan_load(files, [], {"seed_v1", "places_v1"})
    assert plan["errors"] == [] and len(plan["warnings"]) == 1


def test_tag_missing_from_its_loaded_source_is_deleted():
    existing = [stored("Pune", "places_v1"), stored("Agra", "places_v1")]
    plan = plan_load({"seed_v1": [], "places_v1": [row("Pune")]}, existing, {"places_v1"})
    res = plan["sources"]["places_v1"]
    assert res["delete"] == ["Agra"] and res["unchanged"] == 1


def test_tag_from_a_source_not_in_the_list_is_kept():
    existing = [stored("Promoted Tag", "promoted"), stored("Old Seed", "seed_v1")]
    plan = plan_load({"seed_v1": []}, existing, {"seed_v1"})
    assert plan["sources"]["seed_v1"]["delete"] == ["Old Seed"]


def test_tag_of_a_source_that_is_not_loaded_is_kept():
    existing = [stored("Agra", "places_v1")]
    plan = plan_load({"seed_v1": [], "places_v1": []}, existing, {"seed_v1"})
    assert "places_v1" not in plan["sources"]


def test_changed_tag_is_an_update_and_same_tag_is_unchanged():
    existing = [stored("Pune", "places_v1"), stored("Agra", "places_v1")]
    plan = plan_load({"places_v1": [row("Pune", desc="new"), row("Agra")]}, existing, {"places_v1"})
    res = plan["sources"]["places_v1"]
    assert [r["tag"] for r in res["update"]] == ["Pune"] and res["unchanged"] == 1 and res["insert"] == []


def test_file_tag_that_exists_under_another_source_is_an_error():
    plan = plan_load({"places_v1": [row("Pune")]}, [stored("Pune", "seed_v1")], {"places_v1"})
    assert len(plan["errors"]) == 1


def test_sources_have_distinct_names_and_the_seed_keeps_its_stored_value():
    names = [s[0] for s in SOURCES]
    assert len(set(names)) == len(names) and names[0] == "seed_v1"
    assert dict((n, st) for n, _, st in SOURCES)["seed_v1"] == "reviewed"


def test_a_renamed_tag_is_renamed_in_place_and_not_deleted():
    files = {"seed_v1": [row("Finance Bill", aliases=["Financial Bill"], typ="law")]}
    plan = plan_load(files, [stored("Financial Bill", "seed_v1", typ="law")], {"seed_v1"})
    res = plan["sources"]["seed_v1"]
    assert [(r["old"], r["tag"]) for r in res["rename"]] == [("Financial Bill", "Finance Bill")]
    assert res["insert"] == [] and res["delete"] == [] and plan["errors"] == []


def test_an_alias_that_is_still_a_tag_of_the_file_is_no_rename():
    files = {"seed_v1": [row("Railway Budget", aliases=["Rail Budget"]), row("Rail Budget")]}
    existing = [stored("Railway Budget", "seed_v1"), stored("Rail Budget", "seed_v1")]
    res = plan_load(files, existing, {"seed_v1"})["sources"]["seed_v1"]
    assert res["rename"] == [] and res["insert"] == []

import pytest

from scripts.apply_tag_merges import check_names, split_group
from scripts.link_entities import norm_name
from scripts.load_tags import apply_groups
from tag_merges import load_groups, merged_aliases, resolve


def m(a, b, new_name="", new_type="", note=""):
    return {"tag_from": a, "tag_into": b, "new_name": new_name, "new_type": new_type, "note": note}


def test_a_chain_goes_into_its_last_tag():
    [g] = resolve([m("Rapid Transit System", "Metro Railways"), m("Metro Railways", "Metro Railway Development")], [])
    assert g.target == "Metro Railway Development"
    assert g.members == ["Metro Railways", "Rapid Transit System"]


def test_a_loop_needs_a_target_row():
    loop = [m("Encroachment", "Land Encroachment"), m("Land Encroachment", "Unauthorized Encroachments"),
            m("Unauthorized Encroachments", "Encroachment")]
    with pytest.raises(ValueError, match="needs a row"):
        resolve(loop, [])
    [g] = resolve(loop, [{"target": "Land Encroachment", "new_name": ""}])
    assert g.target == "Land Encroachment" and g.members == ["Encroachment", "Unauthorized Encroachments"]


def test_a_tag_with_two_targets_joins_both_into_one_group():
    rows = [m("SC&ST", "Scheduled Castes and Scheduled Tribes"), m("SC&ST", "SC & ST Welfare")]
    with pytest.raises(ValueError, match="needs a row"):
        resolve(rows, [])
    [g] = resolve(rows, [{"target": "Scheduled Castes and Scheduled Tribes", "new_name": ""}])
    assert g.members == ["SC & ST Welfare", "SC&ST"]


def test_a_target_row_can_override_the_end_of_the_chain_and_rename():
    rows = [m("ST", "Scheduled Tribes"), m("Scheduled Tribes", "Tribals")]
    [g] = resolve(rows, [{"target": "Scheduled Tribes", "new_name": ""}])
    assert g.target == "Scheduled Tribes" and g.members == ["ST", "Tribals"]
    [g] = resolve([m("Support Prices", "MSP  x")], [{"target": "MSP  x", "new_name": "MSP x"}])
    assert g.final_name == "MSP x"


def test_the_new_name_of_a_merge_row_renames_the_kept_tag_and_a_name_equal_to_the_target_is_no_rename():
    [g] = resolve([m("Budget", "General Budget", "Union Budget", "topic")], [])
    assert (g.final_name, g.new_type) == ("Union Budget", "topic")
    [g] = resolve([m("Non-Resident Indians", "NRIs", "NRIs")], [])
    assert g.new_name is None


def test_a_target_row_for_a_tag_in_no_group_is_an_error():
    with pytest.raises(ValueError, match="in no group"):
        resolve([m("A", "B")], [{"target": "C", "new_name": ""}])


def test_the_real_files_resolve():
    groups = load_groups()
    assert len(groups) == 173 and sum(len(g.members) for g in groups) == 183
    finals = [g.final_name for g in groups]
    assert len(set(finals)) == len(finals)


def test_merged_aliases_add_the_merged_names_and_the_old_name_once():
    out = merged_aliases(["Budget 2019"], "General Budget", "Union Budget",
                         [("Budget", ["union budget", "General budget"])], norm_name)
    assert out == ["Budget 2019", "General Budget", "Budget"]


def test_a_split_vote_inside_one_group_is_found():
    group_of = {1: 0, 2: 0, 3: 1}
    assert split_group([{"tag_id": 1, "p": 0.45}, {"tag_id": 2, "p": 0.3}, {"tag_id": 3, "p": 0.1}], group_of, 0.7) == 0
    assert split_group([{"tag_id": 1, "p": 0.75}, {"tag_id": 9, "p": 0.2}], group_of, 0.7) is None
    assert split_group([{"tag_id": 1, "p": 0.4}, {"tag_id": 2, "p": 0.2}], group_of, 0.7) is None
    assert split_group([{"tag_id": None, "p": 0.9}], group_of, 0.7) is None


def test_check_names_accepts_a_kept_tag_that_a_first_run_renamed():
    [g] = resolve([m("Budget", "General Budget", "Union Budget")], [])
    before = {"Budget": {}, "General Budget": {}}
    after = {"Budget": {}, "Union Budget": {}}
    assert check_names([g], before) == [] and check_names([g], after) == []
    assert check_names([g], {"Budget": {}, "General Budget": {}, "Union Budget": {}})


def row(tag, aliases=(), typ="topic"):
    return {"tag": tag, "type": typ, "subtype": None, "domain": None, "description": "d",
            "aliases": list(aliases), "debate_count": 0}


def test_the_loader_gives_the_kept_tag_its_merged_name_and_aliases():
    [g] = resolve([m("Budget", "General Budget", "Union Budget", "topic")], [])
    files = {"seed_v1": [row("Budget", ["Budgets"]), row("General Budget", typ="law"), row("Roads")]}
    out = apply_groups(files, [g])["seed_v1"]
    assert [r["tag"] for r in out] == ["Budget", "Union Budget", "Roads"]
    assert out[1]["type"] == "topic" and out[1]["aliases"] == ["General Budget", "Budget", "Budgets"]


def test_the_loader_skips_a_group_whose_tags_are_not_all_in_the_lists():
    [g] = resolve([m("Budget", "General Budget")], [])
    files = {"seed_v1": [row("General Budget")]}
    assert apply_groups(files, [g]) == files

from scripts.build_new_tags import check_domains, final_rows, new_tags, parse_edit, to_row


def review(name="", decision="new", type_="topic", domain="Railways", review_="ok", note="", ids="1 2", tag=""):
    return {"name_ids": ids, "decision": decision, "tag": tag, "name": name, "type": type_, "domain": domain,
            "review": review_, "review_note": note}


def test_parse_edit_reads_the_field_pairs_and_ignores_the_reason():
    note = "decision=new | name=District Magistrate | type=role | aliases=District Collector | reason: one office"
    assert parse_edit(note) == {"decision": "new", "name": "District Magistrate", "type": "role",
                                "aliases": "District Collector"}
    assert parse_edit("keep decision=existing | tag=President's Rule | reason: x") == {
        "decision": "existing", "tag": "President's Rule"}


def test_an_edit_turns_an_existing_row_into_a_new_tag():
    rows = final_rows([review(decision="existing", tag="Displaced People", type_="", domain="", review_="edit",
                              note="decision=new | name=Rehabilitation of Displaced Persons | reason: x")])
    assert rows[0]["decision"] == "new" and rows[0]["name"] == "Rehabilitation of Displaced Persons"
    assert rows[0]["edited"]


def test_two_rows_of_one_name_make_one_tag_and_the_edited_row_wins():
    rows = final_rows([review("Andhra Pradesh Reorganisation Act", domain="Law, Justice and Constitution", ids="1"),
                       review("Andhra Pradesh Reorganisation Act", domain="", review_="edit", ids="2",
                              note="domain=Home Affairs and Law and Order | reason: x")])
    tags, problems = new_tags(rows, [])
    assert problems == [] and len(tags) == 1
    assert tags[0]["domain"] == "Home Affairs and Law and Order" and tags[0]["name_ids"] == ["2", "1"]


def test_two_different_values_without_an_edit_are_a_problem():
    rows = final_rows([review("X", domain="Railways", ids="1"), review("X", domain="Defence", ids="2")])
    _, problems = new_tags(rows, [])
    assert problems == ["'X': two values for domain: ['Defence', 'Railways']"]


def test_a_fill_gives_a_missing_type_and_domain():
    rows = final_rows([review("Road Infrastructure", type_="", domain="")])
    fills = [{"tag": "Road Infrastructure", "field": "type", "value": "topic"},
             {"tag": "Road Infrastructure", "field": "domain", "value": "Roads and Highways"}]
    tags, problems = new_tags(rows, fills)
    assert problems == [] and (tags[0]["type"], tags[0]["domain"]) == ("topic", "Roads and Highways")
    _, problems = new_tags(rows, [])
    assert problems == ["'Road Infrastructure': no type", "'Road Infrastructure': no domain"]


def test_aliases_come_from_the_edit_and_an_unknown_type_or_domain_is_a_problem():
    rows = final_rows([review("District Magistrate", type_="role", review_="edit",
                              note="aliases=District Collector | reason: x")])
    tags, _ = new_tags(rows, [])
    assert tags[0]["aliases"] == ["District Collector"]
    _, problems = new_tags(final_rows([review("Y", type_="thing")]), [])
    assert problems == ["'Y': unknown type 'thing'"]
    assert check_domains([{"tag": "Z", "domain": "Nowhere"}], {"Railways"}) == ["'Z': unknown domain 'Nowhere'"]


def test_rows_that_are_not_new_make_no_tag():
    rows = final_rows([review("A", decision="existing", tag="Railways"), review("B", decision="general")])
    assert new_tags(rows, []) == ([], [])


def test_to_row_uses_the_columns_of_the_seed_list():
    t = {"tag": "Khetauri", "type": "group", "subtype": "", "domain": "Tribal Affairs", "aliases": [],
         "debate_count": "0"}
    assert to_row(t, "A community.") == {"tag": "Khetauri", "type": "group", "subtype": "", "domain": "Tribal Affairs",
                                        "description": "A community.", "aliases": "-", "debate_count": "0"}


def test_a_new_name_equal_to_a_name_or_alias_of_another_list_is_a_problem():
    from scripts.build_new_tags import check_names
    other = [{"tag": "Finance Bill", "aliases": "Financial Bill"}, {"tag": "Mumbai City", "aliases": "-"}]
    tags = [{"tag": "Finance Bill"}, {"tag": "financial bill."}, {"tag": "Khetauri"}]
    assert check_names(tags, other) == ["'Finance Bill': equals the name or an alias of the tag 'Finance Bill'",
                                        "'financial bill.': equals the name or an alias of the tag 'Finance Bill'"]

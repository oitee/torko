import pytest

from scripts.build_seed_tags import apply_edit, assemble, check_cover, finish, pack_merge_input, split_chunks


def group(tag, aliases=(), typ="topic", domain="Energy"):
    return {"tag": tag, "type": typ, "subtype": "", "domain": domain, "description": "d", "aliases": list(aliases)}


def test_split_chunks_keeps_order_in_files_of_400():
    raw = [[f"t{i}", "2"] for i in range(401)]
    chunks = split_chunks(raw)
    assert list(chunks) == ["chunk_00", "chunk_01"]
    assert chunks["chunk_00"][0] == "t0\t2" and chunks["chunk_01"] == ["t400\t2"]


def test_pack_never_splits_a_group_and_fills_the_first_file_with_room():
    rows = [[f"a{i}", "topic", "Energy", "d", "-"] for i in range(300)]
    rows += [[f"b{i}", "topic", "Defence", "d", "-"] for i in range(100)]
    rows += [[f"c{i}", "topic", "Railways", "d", "-"] for i in range(50)]
    files = pack_merge_input(rows, {})
    assert {k: len(v) for k, v in files.items()} == {"topic__energy_plus1": 350, "topic__defence": 100}


def test_pack_marks_a_changed_spelling_with_a_question_mark():
    files = pack_merge_input([["NFDC", "institution", "-", "d", "-"]], {"Nfdc": 3})
    assert files["institution__"] == ["NFDC\t?\t-\td\t-"]


def test_assemble_attaches_a_changed_spelling_and_drops_a_double():
    merged = [["NFDC", "institution", "-", "d", "-", "?"],
              ["Roads", "topic", "-", "d", "Road Works", "5"],
              ["Road Works", "topic", "-", "d", "-", "2"]]
    groups, log = assemble(merged, {"Nfdc": 3, "Roads": 3, "Road Works": 2})
    by_tag = {g["tag"]: g for g in groups}
    assert by_tag["NFDC"]["aliases"] == ["Nfdc"]
    assert "Road Works" not in by_tag
    assert any(line.startswith("attached: 'Nfdc'") for line in log)
    assert any("'Road Works' is in an earlier group. Group removed." in line for line in log)


def test_assemble_logs_a_keyword_that_it_cannot_place():
    _groups, log = assemble([["Roads", "topic", "-", "d", "-", "3"]], {"Roads": 3, "Lost Tag": 1})
    assert "UNATTACHED: 'Lost Tag'" in log


def test_merge_edit_moves_the_name_and_its_aliases_into_the_target():
    groups = {"Panchayats": group("Panchayats"), "Gram Panchayats": group("Gram Panchayats", ["Gram Panchayat"])}
    apply_edit(groups, "Gram Panchayats", "merge", "Panchayats")
    assert list(groups) == ["Panchayats"]
    assert groups["Panchayats"]["aliases"] == ["Gram Panchayats", "Gram Panchayat"]


def test_an_edit_for_an_unknown_tag_stops_the_build():
    with pytest.raises(SystemExit):
        apply_edit({}, "No Such Tag", "type", "group")


def test_todo_edit_changes_nothing():
    groups = {"A": group("A")}
    apply_edit(groups, "Anything", "todo", "split later")
    assert groups == {"A": group("A")}


def test_cover_check_finds_a_lost_keyword_and_a_count_that_does_not_balance():
    counts = {"A": 2, "B": 3}
    final = finish([group("A")], counts)
    problems = check_cover(final, counts)
    assert "keyword in no group: 'B'" in problems
    assert any(p.startswith("debate counts do not balance") for p in problems)


def test_cover_check_passes_when_each_keyword_appears_one_time():
    counts = {"A": 2, "B": 3}
    final = finish([group("A", ["B"])], counts)
    assert final[0]["debate_count"] == 5
    assert check_cover(final, counts) == []


def test_drop_returns_every_name_and_the_cover_check_allows_them():
    counts = {"A": 2, "B": 3, "Agenda": 4, "Agendas": 1}
    groups = {"A": group("A", ["B"]), "Agenda": group("Agenda", ["Agendas"])}
    removed = apply_edit(groups, "Agenda", "drop", "")
    assert removed == ["Agenda", "Agendas"]
    final = finish(list(groups.values()), counts)
    assert check_cover(final, counts, frozenset(removed)) == []
    assert check_cover(final, counts) != []


def test_split_moves_one_alias_into_a_new_group():
    groups = {"Environmental Protection": group("Environmental Protection", ["Conservation", "Nature Protection"])}
    apply_edit(groups, "Environmental Protection", "split", "Conservation")
    assert groups["Environmental Protection"]["aliases"] == ["Nature Protection"]
    assert groups["Conservation"]["aliases"] == [] and groups["Conservation"]["domain"] == "Energy"


def test_split_of_a_name_that_is_not_an_alias_stops_the_build():
    with pytest.raises(SystemExit):
        apply_edit({"A": group("A")}, "A", "split", "B")


def test_assemble_removes_outer_spaces_from_a_tag_name_and_keeps_the_source_spelling():
    merged = [[" Caste Census", "law", "-", "d", "-", "10"]]
    groups, log = assemble(merged, {" Caste Census": 10})
    assert groups[0]["tag"] == "Caste Census"
    assert groups[0]["aliases"] == [" Caste Census"]
    assert check_cover(finish(groups, {" Caste Census": 10}), {" Caste Census": 10}) == []
    assert any("outer spaces removed: ' Caste Census'" in line for line in log)


def test_assemble_stops_when_a_trimmed_name_is_the_name_of_another_group():
    merged = [["Land Pooling ", "topic", "-", "d", "-", "2"], ["Land Pooling", "topic", "-", "d", "-", "3"]]
    with pytest.raises(SystemExit):
        assemble(merged, {"Land Pooling ": 2, "Land Pooling": 3})

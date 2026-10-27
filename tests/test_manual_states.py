import csv

import pytest

from scripts.load_party_history import MANUAL_STATES, read_manual_states


def _write(path, rows):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["term", "mpsno", "name", "state"], delimiter="\t")
        w.writeheader()
        w.writerows(rows)


def test_only_filled_rows_are_returned(tmp_path):
    p = tmp_path / "m.tsv"
    _write(p, [{"term": "13", "mpsno": "524", "name": "A", "state": " Uttar Pradesh "},
               {"term": "13", "mpsno": "552", "name": "B", "state": ""}])
    assert read_manual_states(p) == [{"term": 13, "mpsno": 524, "state": "Uttar Pradesh"}]


def test_two_rows_for_one_member_and_term_stop_the_load(tmp_path):
    p = tmp_path / "m.tsv"
    _write(p, [{"term": "13", "mpsno": "524", "name": "A", "state": ""},
               {"term": "13", "mpsno": "524", "name": "A", "state": "Bihar"}])
    with pytest.raises(SystemExit):
        read_manual_states(p)


def test_the_tracked_file_reads():
    read_manual_states(MANUAL_STATES)


def test_every_source_spelling_has_a_fixed_name():
    import glob
    import json

    from scripts.load_party_history import TSV, read_state_names

    spellings = read_state_names()
    with open(TSV, encoding="utf-8", newline="") as f:
        used = {r["state"] for r in csv.DictReader(f, delimiter="\t") if r["state"]}
    for path in glob.glob(str(TSV.parent.parent / "raw" / "sansad_ls*.json")):
        with open(path, encoding="utf-8") as f:
            used |= {(m.get("stateName") or "").strip() for m in json.load(f)} - {""}
    assert used - set(spellings) == set()


def test_each_fixed_name_maps_to_itself():
    from scripts.load_party_history import read_state_names

    spellings = read_state_names()
    assert all(spellings.get(n) == n for n in set(spellings.values()) if n)
    assert spellings["Orissa"] == "Odisha" and spellings["NCT of Delhi"] == "Delhi"
    assert spellings["Nominated"] == ""


def test_state_tag_ids_reads_tag_names_through_the_map_and_drops_ties():
    from scripts.load_party_history import state_tag_ids

    spellings = {"Pondicherry": "Puducherry", "Puducherry": "Puducherry", "Delhi": "Delhi", "Goa": "Goa"}
    tags = [(1, "Pondicherry"), (2, "Delhi"), (3, "Delhi"), (4, "Goa")]
    assert state_tag_ids(["Puducherry", "Delhi", "Goa"], tags, spellings) == {"Puducherry": 1, "Goa": 4}


def test_state_id_of():
    from scripts.load_party_history import state_id_of

    spellings, ids = {"Orissa": "Odisha", "Odisha": "Odisha", "Nominated": ""}, {"Odisha": 7}
    assert state_id_of("Orissa ", spellings, ids, "x") == 7
    assert state_id_of("", spellings, ids, "x") is None
    assert state_id_of("Nominated", spellings, ids, "x") is None
    with pytest.raises(SystemExit):
        state_id_of("Oddisha", spellings, ids, "x")

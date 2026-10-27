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


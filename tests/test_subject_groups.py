"""Offline tests for the pure functions of scripts/subject_groups.py."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import subject_groups as sg


def test_union_groups_joins_chain_and_keeps_singletons():
    groups = sg.union_groups([1, 2, 3, 4, 5], [(1, 2), (2, 3)])
    assert groups == [[1, 2, 3], [4], [5]]


def test_union_groups_ignores_unknown_ids():
    assert sg.union_groups([1, 2], [(1, 9)]) == [[1], [2]]


def test_mutual_edges_need_both_directions():
    neigh = {1: [(2, 0.05), (3, 0.05)], 2: [(1, 0.06)], 3: [(4, 0.01)], 4: []}
    assert sg.mutual_edges(neigh, 0.1) == [(1, 2, 0.06)]


def test_mutual_edges_respect_limit():
    neigh = {1: [(2, 0.12)], 2: [(1, 0.12)]}
    assert sg.mutual_edges(neigh, 0.1) == []
    assert len(sg.mutual_edges(neigh, 0.13)) == 1


def test_guard_splits_a_chain_with_loose_links():
    ids = list(range(10))
    edges = [(i, i + 1, 0.12 if i == 4 else 0.03) for i in range(9)]
    assert len(sg.group_with_guard(ids, edges, 0.14, max_size=6)) == 2
    assert len(sg.group_with_guard(ids, edges, 0.14, max_size=20)) == 1


def test_guard_stops_at_min_d():
    ids = list(range(10))
    edges = [(i, i + 1, 0.03) for i in range(9)]
    groups = sg.group_with_guard(ids, edges, 0.14, max_size=3, step=0.05, min_d=0.04)
    assert groups == [ids]


def test_parent_is_tag_with_most_distinct_speeches():
    tag_of = {1: "Arrears", 2: "Arrears", 3: "Wages", 4: None}
    sp = {1: {1, 2}, 2: {2, 3}, 3: {9}, 4: {7, 8, 9}}
    parent, share, others = sg.choose_parent([1, 2, 3, 4], tag_of, sp)
    assert parent == "Arrears" and others == ["Wages"]
    assert abs(share - 3 / 4) < 1e-9


def test_parent_none_without_linked_member():
    assert sg.choose_parent([1], {1: None}, {1: {1}}) == (None, 0.0, [])


def test_label_is_most_speeches_then_shortest():
    name_of = {1: "A long name", 2: "Short", 3: "Other"}
    n = {1: 5, 2: 5, 3: 2}
    assert sg.choose_label([1, 2, 3], name_of, n) == "Short"

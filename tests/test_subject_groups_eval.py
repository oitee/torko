from scripts.subject_groups_eval import bin_pairs, edges_for, score


NEIGH = {1: [(2, 0.05), (3, 0.15)], 2: [(1, 0.06), (3, 0.35)], 3: [(1, 0.15)]}


def test_bin_pairs_keeps_each_pair_once_with_the_smaller_distance():
    bins = bin_pairs(NEIGH, bin_width=0.1, n_bins=3)
    assert bins[0] == [(1, 2, 0.05)]
    assert sorted(bins[1]) == [(1, 3, 0.15)]
    assert 2 not in bins


def test_mutual_edges_need_both_directions():
    assert sorted(edges_for(NEIGH, k=2, mutual=True)) == [(1, 2, 0.06), (1, 3, 0.15)]
    assert (2, 3, 0.35) in edges_for(NEIGH, k=2, mutual=False)


def test_k_limits_the_neighbours():
    assert edges_for(NEIGH, k=1, mutual=True) == [(1, 2, 0.06)]


def test_score_counts_joined_and_missed_pairs_with_weights():
    s = score([[1, 2]], [(1, 2, True, 2.0), (1, 3, True, 1.0), (2, 4, False, 5.0)])
    assert (s["tp"], s["fp"], s["fn"]) == (2.0, 0.0, 1.0)
    assert s["precision"] == 1.0
    s = score([[1, 2, 3]], [(1, 3, False, 1.0), (1, 2, True, 1.0)])
    assert s["fp"] == 1.0 and s["precision"] == 0.5

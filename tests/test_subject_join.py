from scripts.subject_join import join_units, unit_line, weighted_pr


def test_unit_line_shows_at_most_twelve_names():
    names = [(f"n{i}", 20 - i) for i in range(14)]
    line = unit_line(names)
    assert line.startswith("n0 (20); n1 (19)")
    assert line.endswith("(+2 more names)")
    assert "n12" not in line


def test_join_units_joins_the_nearest_pairs_first_and_respects_the_size_limit():
    subjects = join_units(3, [(0, 1, 0.05), (1, 2, 0.06)], sizes=[10, 10, 25], max_joined=30)
    assert sorted(sorted(s) for s in subjects) == [[0, 1], [2]]


def test_join_units_chains_when_the_size_allows():
    subjects = join_units(3, [(0, 1, 0.05), (1, 2, 0.06)], sizes=[2, 2, 2], max_joined=40)
    assert [sorted(s) for s in subjects] == [[0, 1, 2]]


def test_weighted_pr_uses_the_band_weights():
    gold = [("P1", 0.05, True, 1.0), ("P2", 0.15, False, 10.0), ("P3", 0.15, True, 10.0)]
    r = weighted_pr(gold, lambda pid, d: d < 0.10)
    assert r == {"precision": 1.0, "recall": round(1 / 11, 3)}
    r = weighted_pr(gold, lambda pid, d: True)
    assert r["precision"] == round(11 / 21, 3)


def test_joins_find_units_by_their_name_ids_and_skip_lost_units():
    from scripts.subject_join import joins_to_pairs, unit_key
    units = [[5, 3], [9], [7, 8]]
    assert unit_key(units[0]) == "3 5"
    rows = [{"name_ids_a": "3 5", "name_ids_b": "9", "centre_distance": "0.1"},
            {"name_ids_a": "7 8", "name_ids_b": "1 2", "centre_distance": "0.2"}]
    pairs, unmatched = joins_to_pairs(units, rows)
    assert pairs == [(0, 1, 0.1)] and unmatched == 1


def test_a_cannot_link_stops_a_chain_join():
    pairs = [(0, 1, 0.05), (1, 2, 0.06)]
    subjects = join_units(3, pairs, sizes=[2, 2, 2], cannot={frozenset((0, 2))})
    assert sorted(sorted(s) for s in subjects) == [[0, 1], [2]]


def test_a_cannot_link_between_other_subjects_does_not_matter():
    subjects = join_units(4, [(0, 1, 0.05)], sizes=[1, 1, 1, 1], cannot={frozenset((2, 3))})
    assert sorted(sorted(s) for s in subjects) == [[0, 1], [2], [3]]



def test_the_final_label_prefers_an_llm_label_for_the_exact_name_set():
    from scripts.subject_join import choose_final_label, name_key
    assert name_key("12 3 7") == "3 7 12"
    labels = {"3 7": ("Sugarcane farmers' arrears", "llm")}
    assert choose_final_label("3 7", 2, "Sugarcane farmers' dues", labels) == ("Sugarcane farmers' arrears", "llm")
    assert choose_final_label("3 8", 2, "Wage arrears", labels) == ("Wage arrears", "auto")
    assert choose_final_label("9", 1, "Cheque bouncing", labels) == ("Cheque bouncing", "name")


def test_job_files_name_the_output_file_relative_to_the_job_folder(tmp_path):
    from scripts.subject_join import write_jobs
    assert write_jobs(tmp_path, [("C1", "A: x\nB: y")], "PAIR") == 1
    lines = (tmp_path / "jobs" / "j0001.txt").read_text(encoding="utf-8").splitlines()
    assert lines[1] == "Write one JSON line per pair, in this order, to out/j0001.out.jsonl"


def test_known_answers_read_both_files_by_name_ids_and_a_different_answer_wins(tmp_path):
    from scripts.subject_join import known_answers
    units = [[5, 3], [9], [7, 8], [4]]
    joins = tmp_path / "joins.tsv"
    joins.write_text("name_ids_a\tname_ids_b\tcentre_distance\tconfidence\n"
                     "3 5\t9\t0.1\thigh\n7 8\t4\t0.1\thigh\n1 2\t9\t0.1\thigh\n", encoding="utf-8")
    cannot = tmp_path / "cannot.tsv"
    cannot.write_text("name_ids_a\tname_ids_b\tsource\tconfidence\n7 8\t4\tchain\tlow\n", encoding="utf-8")
    known = known_answers(units, joins, cannot)
    assert known == {frozenset((0, 1)): "same", frozenset((2, 3)): "different"}


def test_known_answers_with_no_files_is_empty(tmp_path):
    from scripts.subject_join import known_answers
    assert known_answers([[1], [2]], tmp_path / "none.tsv", tmp_path / "none2.tsv") == {}


def test_merge_pair_rows_keeps_old_joins_that_the_new_answers_do_not_cover():
    from scripts.subject_join import merge_pair_rows
    new = [{"name_ids_a": "1 2", "name_ids_b": "3", "centre_distance": "0.1", "confidence": "high"}]
    old = [{"name_ids_a": "3", "name_ids_b": "1 2", "centre_distance": "0.2", "confidence": "low"},
           {"name_ids_a": "7", "name_ids_b": "8 9", "centre_distance": "0.1", "confidence": "high"}]
    rows, kept = merge_pair_rows(new, old)
    assert kept == 1
    assert rows == [new[0], old[1]]


def test_chain_ingest_keeps_the_old_cannot_links(tmp_path, monkeypatch):
    import argparse
    import json
    import pickle
    import scripts.subject_join as sj
    results, data = tmp_path / "results", tmp_path / "data"
    results.mkdir()
    data.mkdir()
    monkeypatch.setattr(sj, "RESULTS", results)
    monkeypatch.setattr(sj, "JOINS", data / "joins.tsv")
    monkeypatch.setattr(sj, "CANNOT", data / "cannot.tsv")
    units = [[1], [2], [3]]
    cache = tmp_path / "units.pkl"
    cache.write_bytes(pickle.dumps({"units": units}))
    (data / "joins.tsv").write_text("name_ids_a\tname_ids_b\tcentre_distance\tconfidence\n1\t2\t0.1\thigh\n2\t3\t0.1\thigh\n")
    (data / "cannot.tsv").write_text("name_ids_a\tname_ids_b\tsource\tconfidence\n7\t8\tchain\thigh\n")
    (results / "join_candidates_v1.tsv").write_text("pair_id\tunit_a\tunit_b\nP1\t0\t1\nP2\t1\t2\n")
    (results / "join_llm_v1.tsv").write_text("pair_id\tdecision\tconfidence\nP1\tsame\thigh\nP2\tsame\thigh\n")
    (results / "chain_pairs_v1.tsv").write_text("pair_id\tunit_a\tunit_b\nC1\t0\t2\n")
    folder = tmp_path / "chains"
    (folder / "out").mkdir(parents=True)
    (folder / "out" / "j0001.out.jsonl").write_text(json.dumps({"pair": "C1", "decision": "different", "confidence": "low"}) + "\n")
    sj.chain_ingest(argparse.Namespace(cache=cache, folder=folder))
    lines = (data / "cannot.tsv").read_text().splitlines()
    assert lines == ["name_ids_a\tname_ids_b\tsource\tconfidence", "1\t3\tchain\tlow", "7\t8\tchain\thigh"]


def test_merge_labels_keeps_old_labels_and_a_new_label_wins():
    from scripts.subject_join import merge_labels
    labels, kept = merge_labels({"1 2": ("New", "llm")}, {"1 2": ("Old", "llm"), "3 4": ("Other", "llm")})
    assert kept == 1
    assert labels == {"1 2": ("New", "llm"), "3 4": ("Other", "llm")}


def label_files(tmp_path, monkeypatch):
    import scripts.subject_join as sj
    results, data = tmp_path / "results", tmp_path / "data"
    results.mkdir()
    data.mkdir()
    monkeypatch.setattr(sj, "RESULTS", results)
    monkeypatch.setattr(sj, "LABELS", data / "labels.tsv")
    monkeypatch.setattr(sj, "LABEL_SUBJECTS", results / "label_subjects.tsv")
    (results / "subjects_v1.tsv").write_text(
        "subject_id\tn_names\tnames\tname_ids\n"
        "S00001\t2\tDues (5) | Arrears (3)\t7 3\n"
        "S00002\t2\tRail fare (4) | Train fare (2)\t5 9\n"
        "S00003\t1\tCheque bouncing (2)\t8\n", encoding="utf-8")
    (data / "labels.tsv").write_text("name_ids\tlabel\tsource\n5 9\tRailway fares\tllm\n1 2\tLost subject\tllm\n",
                                     encoding="utf-8")
    return sj, results, data


def test_label_jobs_skip_subjects_with_a_stored_label(tmp_path, monkeypatch):
    import argparse
    sj, results, _ = label_files(tmp_path, monkeypatch)
    sj.label_jobs(argparse.Namespace(folder=tmp_path / "jobs"))
    assert (results / "label_subjects.tsv").read_text().splitlines() == ["subject_id\tname_ids", "S00001\t3 7"]
    assert (tmp_path / "jobs" / "jobs" / "j0001.txt").read_text().startswith("SUBJECTS: S00001\n")


def test_labels_ingest_reads_the_job_subjects_and_keeps_the_old_labels(tmp_path, monkeypatch):
    import argparse
    import json
    sj, results, data = label_files(tmp_path, monkeypatch)
    sj.label_jobs(argparse.Namespace(folder=tmp_path / "jobs"))
    (results / "subjects_v1.tsv").write_text("subject_id\tn_names\tnames\tname_ids\n", encoding="utf-8")
    (tmp_path / "jobs" / "out" / "j0001.out.jsonl").write_text(json.dumps({"subject": "S00001", "label": "Dues"}) + "\n")
    sj.labels_ingest(argparse.Namespace(folder=tmp_path / "jobs", relabels=None))
    assert (data / "labels.tsv").read_text().splitlines() == [
        "name_ids\tlabel\tsource", "1 2\tLost subject\tllm", "3 7\tDues\tllm", "5 9\tRailway fares\tllm"]

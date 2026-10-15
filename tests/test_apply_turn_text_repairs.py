import json
import re
from pathlib import Path

import pytest

from scripts.apply_turn_text_repairs import (
    FIELDS,
    TSV,
    decode_text,
    encode_text,
    new_layout,
    plan_debate,
    read_rows,
    text_hash,
)

CASES = json.loads((Path(__file__).parent / "data" / "turn_text_repairs_cases.json").read_text(encoding="utf-8"))
TRACKED = read_rows(TSV)


def _part(n, txt, garbled="g", **kw):
    return {
        "part": n, "garbled_sha256": text_hash(garbled), "method": "repair-dict",
        "speaker_label": "", "mpsno": "", "role_code": "", "name_source": "", "text": txt, **kw,
    }


def _turns(*texts):
    return [{"id": 100 + i, "seq": i, "text": t} for i, t in enumerate(texts)]


def _after(current, listed):
    by_id = {t["id"]: t["text"] for t in current}
    return [
        {"id": row["id"], "seq": row["seq"], "text": row["part"]["text"] if row["part"] else by_id[row["id"]]}
        for row in new_layout(current, listed)
    ]


def _write(path, lines):
    path.write_text("\t".join(FIELDS) + "\n" + "".join("\t".join(map(str, l)) + "\n" for l in lines), encoding="utf-8")


@pytest.mark.parametrize(
    "s",
    ["", "plain", "a\nb", "tab\there", "back\\slash", "literal \\n is not a new line", "end\\", "\r\n"],
)
def test_encode_then_decode_gives_the_same_text(s):
    encoded = encode_text(s)
    assert "\n" not in encoded and "\t" not in encoded and "\r" not in encoded
    assert decode_text(encoded) == s


def test_read_rows_groups_the_parts_of_a_turn(tmp_path):
    path = tmp_path / "repairs.tsv"
    h = text_hash("garbled")
    _write(path, [
        [13, 1, 1, 4, 0, h, "repair-dict", "", "", "", "", encode_text("Now I call\nupon him.")],
        [13, 1, 1, 4, 1, h, "repair-dict", "प्रधानमंत्री (श्री अटल बिहारी वाजपेयी)", "499", "", "split-seen-label", "माननीय"],
    ])
    [(key, parts)] = read_rows(path).items()
    assert key == (13, 1, 1, 4)
    assert [p["part"] for p in parts] == [0, 1]
    assert parts[0]["text"] == "Now I call\nupon him."
    assert parts[1]["mpsno"] == "499" and parts[1]["speaker_label"].startswith("प्रधानमंत्री")


def test_read_rows_refuses_an_unknown_method(tmp_path):
    path = tmp_path / "repairs.tsv"
    _write(path, [[13, 1, 1, 1, 0, "abc", "repair-guess", "", "", "", "", "x"]])
    with pytest.raises(SystemExit):
        read_rows(path)


def test_read_rows_refuses_a_gap_in_the_parts(tmp_path):
    path = tmp_path / "repairs.tsv"
    _write(path, [
        [13, 1, 1, 1, 0, "abc", "repair-dict", "", "", "", "", "x"],
        [13, 1, 1, 1, 2, "abc", "repair-dict", "", "", "", "unresolved", "y"],
    ])
    with pytest.raises(SystemExit):
        read_rows(path)


def test_read_rows_refuses_a_part_with_a_member_and_a_role(tmp_path):
    path = tmp_path / "repairs.tsv"
    _write(path, [[13, 1, 1, 1, 0, "abc", "repair-dict", "x", "499", "speaker", "presiding", "x"]])
    with pytest.raises(SystemExit):
        read_rows(path)


def test_the_garbled_parser_text_gets_the_parts():
    listed = {1: [_part(0, "a"), _part(1, "b")]}
    assert plan_debate(_turns("x", "g", "y"), listed)[0] == "apply"


def test_the_new_turns_come_right_after_their_turn_and_the_rest_move_down():
    current = _turns("x", "g", "y", "g2")
    listed = {1: [_part(0, "a"), _part(1, "b"), _part(2, "c")], 3: [_part(0, "d", "g2"), _part(1, "e", "g2")]}
    after = _after(current, listed)
    assert [t["text"] for t in after] == ["x", "a", "b", "c", "y", "d", "e"]
    assert [t["seq"] for t in after] == list(range(7))
    assert [t["id"] for t in after] == [100, 101, None, None, 102, 103, None]


def test_a_second_run_finds_the_debate_done():
    current = _turns("x", "g", "y", "g2")
    listed = {1: [_part(0, "a"), _part(1, "b"), _part(2, "c")], 3: [_part(0, "d", "g2"), _part(1, "e", "g2")]}
    assert plan_debate(_after(current, listed), listed) == ("done", {1: "done", 3: "done"})


def test_a_changed_parser_text_skips_the_whole_debate():
    # A parser change that moves one character must not receive the old parts. The other
    # listed turn of the same debate is skipped too, because the seq numbers depend on both.
    listed = {1: [_part(0, "a")], 2: [_part(0, "b", "g2"), _part(1, "c", "g2")]}
    outcome, states = plan_debate(_turns("x", "g ", "g2"), listed)
    assert outcome == "skip"
    assert states == {1: "mismatch", 2: "apply"}


def test_a_missing_turn_is_reported():
    assert plan_debate(_turns("x"), {5: [_part(0, "a")]}) == ("skip", {5: "missing"})


@pytest.mark.parametrize("case", CASES, ids=[c["method"] for c in CASES])
def test_a_real_turn_is_split_and_then_found_done(case):
    key = tuple(case["key"])
    parts = TRACKED[key]
    # The parser numbers the turns of a debate 0, 1, 2, ... with no gap.
    current = [{"id": 10 + s, "seq": s, "text": f"turn {s}"} for s in range(key[3])]
    current += [{"id": 1, "seq": key[3], "text": case["garbled"]}, {"id": 2, "seq": key[3] + 1, "text": "next"}]
    listed = {key[3]: parts}
    assert plan_debate(current, listed)[0] == "apply"
    after = _after(current, listed)
    assert after[-1]["text"] == "next"
    assert plan_debate(after, listed)[0] == "done"


def test_the_tracked_list_is_well_formed():
    assert len(TRACKED) == 1413
    rows = [p for parts in TRACKED.values() for p in parts]
    assert len(rows) == 3566
    assert all(re.fullmatch(r"[0-9a-f]{64}", p["garbled_sha256"]) for p in rows)
    assert all(p["text"].strip() for p in rows)
    for case in CASES:
        parts = TRACKED[tuple(case["key"])]
        assert parts[0]["garbled_sha256"] == text_hash(case["garbled"])
        assert parts[0]["method"] == case["method"]
    # A new turn names its speaker, its role, or says that it has none.
    assert all(p["name_source"] for p in rows if p["part"] > 0)


def test_the_prime_minister_gets_his_own_turn_in_debate_6579():
    speaker, pm = TRACKED[(13, 1, 6579, 1)]
    assert speaker["text"].startswith("Now I call upon Shri Atal Bihari Vajpayee")
    assert speaker["name_source"] == ""  # the parser's speaker stays
    assert pm["mpsno"] == "499" and pm["text"].startswith("माननीय अध्यक्ष जी")


def test_a_label_after_a_question_in_the_same_line_starts_a_new_turn():
    # 13-1-6745-3: the Speaker asks a question, and the Home Minister answers on the same line.
    # The answer must not stay with the Speaker, and the question must not become a label.
    chair, minister = TRACKED[(13, 1, 6745, 3)]
    assert chair["text"] == "Would the Government like to respond to this?"
    assert minister["speaker_label"] == "गृह मंत्री (श्री लाल कृष्ण अडवाणी)"
    assert minister["text"].startswith("मिश्राा जी और पायलट जी")


def test_a_printed_label_that_names_another_member_replaces_the_anchor():
    # 13-1-6679-83: the hidden code names Geeta Mukherjee, but the printed label and the speech
    # are those of Raghuvansh Prasad Singh.
    [part] = TRACKED[(13, 1, 6679, 83)]
    assert part["speaker_label"] == "श्री रघुवंश प्रसाद सिंह (वैशाली)"
    assert part["mpsno"] == "430"

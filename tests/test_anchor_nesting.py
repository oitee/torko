import json
from pathlib import Path

from debate_fetch import close_anchors, split_by_speaker

DATA = Path(__file__).parent / "data"
# Only the anchor code is in the roster. The labels SHRI X and SHRI Z match nobody,
# so a turn gets a code only from an anchor.
ROSTER = [{"mpName": "Shri Yadav Kumar", "mpCode": 2, "mpPartCode": 1}]


def _turns(html: str, roster=ROSTER) -> list[tuple]:
    return [(s.get("mpCode"), s["text"]) for s in split_by_speaker(html, roster)]


class TestCloseAnchors:
    def test_makes_an_anchor_close_itself(self):
        assert close_anchors('<p><A name="3960*9">text') == '<p><A name="3960*9"/>text'

    def test_leaves_html_without_anchors_unchanged(self):
        assert close_anchors("<p>no anchors here</p>") == "<p>no anchors here</p>"

    def test_ignores_case(self):
        assert close_anchors('<a NAME="7*1">') == '<a NAME="7*1"/>'


class TestUnclosedAnchor:
    def test_later_paragraphs_do_not_join_the_anchored_turn(self):
        html = (
            "<p>SHRI X: one.\n"
            '<p><A name="2*1">\n'
            "<p>SHRI YADAV KUMAR: two.\n"
            "<p>SHRI Z: three."
        )
        assert _turns(html) == [(None, "one."), ("2", "two."), (None, "three.")]

    def test_no_text_is_stored_twice(self):
        html = '<p><A name="2*1">\n<p>SHRI X: one.\n<p>SHRI YADAV KUMAR: two.\n<p>SHRI Z: three.'
        texts = [t for _, t in _turns(html)]
        assert texts == ["one.", "two.", "three."]


class TestTrailingAnchor:
    def test_an_anchor_after_the_text_marks_the_next_paragraph(self):
        html = '<p>SHRI X: one.</font>\n<A name="2*1">\n<p>SHRI YADAV KUMAR: two.'
        assert _turns(html) == [(None, "one."), ("2", "two.")]

    def test_an_anchor_before_the_label_stays_with_its_paragraph(self):
        html = '<p><b><A name="2*1"></b><b>SHRI YADAV KUMAR:</b> two.\n<p>SHRI Z: three.'
        assert _turns(html) == [("2", "two."), (None, "three.")]


class TestRealDebate37513:
    def setup_method(self):
        self.html = (DATA / "ls14_37513_slice.html").read_text(encoding="utf-8")
        self.roster = json.loads((DATA / "ls14_37513_roster.json").read_text())
        self.turns = split_by_speaker(self.html, self.roster)

    def test_one_turn_per_speaker(self):
        assert [s["mpCode"] for s in self.turns] == ["4097", "3960", "4178"]

    def test_pathak_turn_holds_no_later_speaker(self):
        pathak = self.turns[0]["text"]
        assert "DEVEGOWDA" not in pathak and "KARUNAKARAN" not in pathak

    def test_devegowda_keeps_his_last_paragraph(self):
        # The anchor of Karunakaran follows this paragraph on the page.
        devegowda = self.turns[1]["text"]
        assert devegowda.startswith("Hon. Chairman, Sir")
        assert "The Minister expressed in his Budget Speech" in devegowda
        assert "The Minister expressed" not in self.turns[2]["text"]

    def test_no_paragraph_is_stored_twice(self):
        words = sum(len(s["text"].split()) for s in self.turns)
        assert words == 459 + 197 + 52

import json
from pathlib import Path

from debate_fetch import split_by_speaker

DATA = Path(__file__).parent / "data"


def _load(html_name: str, roster_name: str):
    html = (DATA / html_name).read_text()
    roster = json.loads((DATA / roster_name).read_text())
    return html, roster


class TestModernReaderDecodesOldFontBody:
    def test_modern_reader_decodes_old_font_body(self):
        html, roster = _load("ls14_32612_slice.html", "ls14_32612_roster.json")
        segs = split_by_speaker(html, roster)
        # Segment 14 is a Chair interjection stored as mojibake that decodes to real Devanagari.
        chair_turns = [
            s for s in segs if s.get("speakerLabel") == "अध्यक्ष महोदय"
        ]
        assert chair_turns, "no decoded Chair label found -- decode pass did not run"
        bodies = [s["text"] for s in chair_turns]
        # Substring match: the turn holds a real paragraph break because the decoder keeps newlines.
        assert any("यह सही नहीं है।" in b for b in bodies), bodies
        # nothing in any turn's text should still carry the ISFOC signature
        for s in segs:
            assert not _looks_like_isfoc_glyphs(s["text"])

    def test_speaker_label_is_decoded(self):
        html, roster = _load("ls14_32612_slice.html", "ls14_32612_roster.json")
        segs = split_by_speaker(html, roster)
        labels = [s.get("speakerLabel") for s in segs]
        assert "अध्यक्ष महोदय" in labels
        # the raw mojibake form must be gone from every stored label
        assert "+ÉvªÉFÉ àÉcÉänªÉ" not in labels

    def test_anchored_mp_name_and_label_come_back_decoded(self):
        # mpCode 42's anchored turn: raw label "gÉÉÒ {É´ÉxÉ BÉÖEàÉÉ® ¤ÉÆºÉãÉ
        # (SÉhbÉÒMÉfÃ)" -> "श्री पवन कुमार बंसल (चण्डीगढ़)" (verified by hand).
        html, roster = _load("ls14_32612_slice.html", "ls14_32612_roster.json")
        segs = split_by_speaker(html, roster)
        bansal = [s for s in segs if s.get("mpCode") == "42" and s.get("nameSource") == "anchor"]
        assert bansal, "the anchored Bansal turn is missing"
        assert bansal[0]["speakerLabel"] == "श्री पवन कुमार बंसल (चण्डीगढ़)"

    def test_decode_pass_does_not_disturb_turn_boundaries(self):
        # Decoding rewrites content, never turn structure, so the segment count is fixed.
        html, roster = _load("ls14_32612_slice.html", "ls14_32612_roster.json")
        segs = split_by_speaker(html, roster)
        assert len(segs) == 38


class TestPresidingDetectedAfterDecode:
    def test_presiding_detected_after_decode(self):
        html = (
            "<p><b>gÉÉÒ {É´ÉxÉ BÉÖEàÉÉ® ¤ÉÆºÉãÉ :</b> ºÉcÉÒ cè*</p>"
            "<p><b>+ÉvªÉFÉ àÉcÉänªÉ :</b> ªÉc ºÉcÉÒ xÉcÉÓ cè*</p>"
        )
        roster = [{"mpName": "Shri Pawan Kumar Bansal", "mpCode": 42, "mpPartCode": 1}]
        segs = split_by_speaker(html, roster)
        chair = [s for s in segs if s.get("speakerLabel") == "अध्यक्ष महोदय"]
        assert len(chair) == 1
        assert chair[0]["nameSource"] == "presiding"
        assert chair[0]["roleCode"] == "speaker"
        assert chair[0]["text"] == "यह सही नहीं है।"


class TestCleanPathUntouched:
    def test_modern_reader_leaves_clean_text_alone(self):
        html, roster = _load("ls18_25_clean.html", "ls18_25_roster.json")
        segs = split_by_speaker(html, roster)
        assert len(segs) == 2
        minister = [s for s in segs if s.get("mpCode") == "4399"]
        assert minister
        assert minister[0]["text"].startswith("Thank you, hon. Chairperson, Sir.")
        assert minister[0]["speakerLabel"] == (
            "THE MINISTER OF STATE OF THE MINISTRY OF LAW AND JUSTICE; AND "
            "MINISTER OF STATE IN THE MINISTRY OF PARLIAMENTARY AFFAIRS "
            "(SHRI ARJUN RAM MEGHWAL)"
        )


def _looks_like_isfoc_glyphs(text: str) -> bool:
    import re

    return bool(re.search(r"ÉÊ|BÉE|àÉ|ºÉ", text))

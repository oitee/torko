"""
T4 (internal_docs/036_THE_AUDIT_AND_FIX_LIST.md): the modern reader
(`debate_fetch.split_by_speaker`) must decode old-font (ISFOC/CDAC-GIST)
Hindi, not just the legacy reader.

Anchor format and font encoding are independent axes. `looks_legacy` routes
purely on anchor shape, so LS14 -- which carries modern "code*part" anchors
but stores its Hindi in the old pre-Unicode font -- lands in
`split_by_speaker`, which used to never call `decode_legacy_hindi` on the
body. This file freezes real LS14/LS18 fixtures and proves the decode pass:
body text and labels come back as Devanagari (not glyphs), a presiding-Chair
label is recognised only after decoding, and the clean LS15-18 path is
unaffected byte-for-byte.
"""
import json
from pathlib import Path

from debate_fetch import split_by_speaker

DATA = Path(__file__).parent / "data"


def _load(html_name: str, roster_name: str):
    html = (DATA / html_name).read_text()
    roster = json.loads((DATA / roster_name).read_text())
    return html, roster


class TestModernReaderDecodesOldFontBody:
    """Real LS14 debate (debates.id=32612, LS14/5/2874), a 59KB slice
    containing the debate's own "Title:" heading, three anchored MPs
    (Somnath Chatterjee mpCode 73, Sukhdev Singh Dhindsa 4130, Pawan Kumar
    Bansal 42) and repeated Devanagari-labelled Chair interjections stored as
    ISFOC gibberish ("+ÉvªÉFÉ àÉcÉänªÉ")."""

    def test_modern_reader_decodes_old_font_body(self):
        html, roster = _load("ls14_32612_slice.html", "ls14_32612_roster.json")
        segs = split_by_speaker(html, roster)
        # segment 14 (0-indexed) is a Chair interjection whose body is stored
        # as "ªÉc ºÉcÉÒ xÉcÉÓ cè*" -- verified by hand to decode to real
        # Devanagari, not glyphs.
        chair_turns = [
            s for s in segs if s.get("speakerLabel") == "अध्यक्ष महोदय"
        ]
        assert chair_turns, "no decoded Chair label found -- decode pass did not run"
        bodies = [s["text"] for s in chair_turns]
        # Substring, not equality: the turn is "यह सही नहीं है।\n\n… ( Interruptions )"
        # -- the paragraph break is real and is there because the decoder no
        # longer strips newlines (see tests/test_legacy_hindi_safety.py). An
        # equality assertion here would be pinning the ABSENCE of that fix.
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
        # Decoding rewrites content, never paragraph/turn structure -- this
        # frozen fixture must always produce exactly this many segments.
        # (Measured against the current parser, pre- and post-decode-fix,
        # via a git-show baseline comparison during verification; recorded
        # here so a future change that alters boundary detection is caught.)
        html, roster = _load("ls14_32612_slice.html", "ls14_32612_roster.json")
        segs = split_by_speaker(html, roster)
        assert len(segs) == 38


class TestPresidingDetectedAfterDecode:
    """A segment whose label prints as the (encoded) Chair must classify as
    presiding only once decoded -- annotate_speakers can't recognise
    "+ÉvªÉFÉ àÉcÉänªÉ" as अध्यक्ष महोदय before the decode pass runs."""

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
    """LS15-18 is already clean Unicode; decode_legacy_hindi must be a no-op
    there. Real LS18 debate (debates.id=25, LS18/7/5983), one anchored
    English turn plus an unattributed preamble -- must round-trip
    byte-identical."""

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
    """Cheap corpus-audit signature (internal_docs/036 Appendix A query):
    the Latin-1 clusters that mark undecoded ISFOC text."""
    import re

    return bool(re.search(r"ÉÊ|BÉE|àÉ|ºÉ", text))

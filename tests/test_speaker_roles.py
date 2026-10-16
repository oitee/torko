import pathlib
import re

import pytest

from debate_fetch import (
    annotate_speakers,
    is_crowd_label,
    is_presiding_label,
    role_code_for_label,
)

_SCHEMA = (
    pathlib.Path(__file__).resolve().parent.parent / "db" / "init" / "02-members.sql"
)


def _sql_text() -> str:
    text = _SCHEMA.read_text()
    start = text.index("CREATE TABLE IF NOT EXISTS speaker_roles")
    end = text.index("ON CONFLICT (code) DO NOTHING;", start)
    return text[start:end]


def _sql_without_comments() -> str:
    return "\n".join(
        line for line in _sql_text().splitlines() if not line.lstrip().startswith("--")
    )


# --- crowd labels -----------------------------------------------------------

@pytest.mark.parametrize(
    "label",
    [
        "SEVERAL HON. MEMBERS",       # 106 in an 8k sample; LS17/5/5987
        "SOME HON. MEMBERS",          # 33
        "अनेक माननीय सदस्य",           # 39; LS16/6/9291
        "कई माननीय सदस्य",             # 7
        "SEVERAL HON . MEMBERS",      # stray space before the period
        "SEVERAL HON'BLE MEMBERS",    # straight apostrophe
        "SEVERAL HON’BLE MEMBERS",    # curly apostrophe
        "MANY HON. MEMBERS",
    ],
)
def test_crowd_labels_are_recognised(label):
    assert is_crowd_label(label)
    assert role_code_for_label(label) == "members_crowd"


@pytest.mark.parametrize(
    "label",
    ["SHRI SHAILENDRA KUMAR", "MR. SPEAKER", "अध्यक्ष महोदय", ""],
)
def test_non_crowd_labels_are_not_crowd(label):
    assert not is_crowd_label(label)


def test_crowd_and_presiding_are_disjoint():
    for label in ["SEVERAL HON. MEMBERS", "अनेक माननीय सदस्य", "SOME HON. MEMBERS"]:
        assert is_crowd_label(label)
        assert not is_presiding_label(label)


# --- canonical offices ------------------------------------------------------

@pytest.mark.parametrize(
    "label,expected",
    [
        ("MR. SPEAKER", "speaker"),                 # 4,280 in an 8k sample
        ("HON. SPEAKER", "speaker"),
        ("MADAM SPEAKER", "speaker"),
        ("अध्यक्ष महोदय", "speaker"),
        ("माननीय अध्यक्ष", "speaker"),               # 2,946; LS17/2/3290
        ("MR. DEPUTY-SPEAKER", "deputy_speaker"),
        ("HON. DEPUTY SPEAKER", "deputy_speaker"),
        ("उपाध्यक्ष महोदय", "deputy_speaker"),
        ("MR. CHAIRMAN", "chairman"),               # 2,917; LS15/7/3991
        ("HON. CHAIRPERSON", "chairman"),
        ("MADAM CHAIRMAN", "chairman"),
        ("सभापति महोदय", "chairman"),
        ("माननीय सभापति", "chairman"),
    ],
)
def test_role_codes(label, expected):
    assert role_code_for_label(label) == expected


@pytest.mark.parametrize(
    "label,expected",
    [
        # Order matters: DEPUTY-SPEAKER contains SPEAKER and उपाध्यक्ष contains अध्यक्ष.
        # Test the deputy forms first.
        ("MR. DEPUTY-SPEAKER", "deputy_speaker"),
        ("उपाध्यक्ष महोदय", "deputy_speaker"),
        # Real corpus form, 58 occurrences in LS13/LS15: the Rajya Sabha officer in a Lok Sabha transcript.
        ("DEPUTY-CHAIRMAN (RAJYA SABHA)", "deputy_chairman"),
        ("DEPUTY CHAIRMAN (RAJYA SABHA)", "deputy_chairman"),
        ("DEPUTY-CHAIRMAN(RAJYA SABHA)", "deputy_chairman"),
    ],
)
def test_deputy_is_not_filed_as_the_principal(label, expected):
    assert role_code_for_label(label) == expected
    assert role_code_for_label(label) not in ("speaker", "chairman")


@pytest.mark.parametrize(
    "label",
    [
        "MR.SPEAKER",                 # no space
        "HON . SPEAKER",              # 326 instances -- stray space
        "M R . CHAIRMAN",             # spaced-out letters
        "MR. D EPUTY-SPEAKER",        # space inside the word
        "HON. DEPUPTY-SPEAKER",       # genuine typo in the source
        "*m75 HON. CHAIRPERSON",      # index-marker prefix glued on
        "*m02 माननीय सभापति",
        "MR> CHAIRMAN",               # '>' for '.'
        "HON.CHAIRPERSON",
    ],
)
def test_the_noisy_tail_still_resolves_to_an_office(label):
    assert is_presiding_label(label)
    assert role_code_for_label(label) is not None


def test_a_real_name_is_not_a_role():
    assert role_code_for_label("SHRI SHAILENDRA KUMAR") is None
    assert not is_presiding_label("SHRI SHAILENDRA KUMAR")


def test_deputy_minister_is_not_a_presiding_officer():
    assert not is_presiding_label("Deputy Minister of Finance")
    assert role_code_for_label("Deputy Minister of Finance") is None


def test_empty_label_is_nothing():
    assert role_code_for_label("") is None
    assert not is_crowd_label("")
    assert not is_presiding_label("")


# --- the annotate pass ------------------------------------------------------

def _seg(label):
    return {"speakerLabel": label, "mpCode": None, "mpName": label}


def test_annotate_tags_crowd_and_presiding_distinctly():
    segs = annotate_speakers(
        [_seg("SEVERAL HON. MEMBERS"), _seg("MR. SPEAKER"), _seg("MR. DEPUTY-SPEAKER")],
        [],
        None,
    )
    assert [s["nameSource"] for s in segs] == ["crowd", "presiding", "presiding"]
    assert [s["roleCode"] for s in segs] == [
        "members_crowd",
        "speaker",
        "deputy_speaker",
    ]
    # Neither kind may ever acquire an mpCode: they are not people.
    assert all(s["mpCode"] is None for s in segs)


def test_role_turns_never_get_an_mpcode():
    segs = annotate_speakers([_seg("MR. SPEAKER")], [], None)
    assert segs[0]["mpCode"] is None
    assert segs[0]["nameSource"] == "presiding"


# --- a frozen real case -----------------------------------------------------

# Verbatim markup from LS13/9/3795, the March 2002 joint sitting.
# The presiding officer is the Rajya Sabha Deputy Chairman.
_JOINT_SITTING_HTML = (
    "<P><FONT SIZE=+1>Let me now remind you, when you accused us of doing a "
    "180 degree turn.… (<I>Interruptions</I>).</FONT>"
    "<P><FONT SIZE=+1>DEPUTY-CHAIRMAN (RAJYA SABHA): Mr. Minister, will you "
    "please go <I>via </I>me?</FONT>"
    "<P><FONT SIZE=+1>SHRI ARUN JAITLEY: Absolutely, Madam.</FONT>"
)


def test_joint_sitting_deputy_chairman_is_its_own_office():
    from debate_fetch_legacy import split_by_speaker_legacy

    segs = split_by_speaker_legacy(_JOINT_SITTING_HTML, [], None)
    by_label = {s["speakerLabel"]: s for s in segs if s.get("speakerLabel")}

    chair = by_label["DEPUTY-CHAIRMAN (RAJYA SABHA)"]
    assert chair["nameSource"] == "presiding"
    assert chair["roleCode"] == "deputy_chairman"
    # Never `chairman`: the Rajya Sabha's Deputy Chairman and a Lok Sabha
    # committee Chairman are two different people.
    assert chair["roleCode"] != "chairman"
    # A role is not a person and must never acquire an mpCode.
    assert chair["mpCode"] is None
    # The real member speaking next must still be read as a person, not a role.
    assert role_code_for_label("SHRI ARUN JAITLEY") is None


def test_rajya_sabha_suffix_is_a_chamber_not_a_person():
    assert role_code_for_label("DEPUTY-CHAIRMAN (RAJYA SABHA)") == "deputy_chairman"
    assert "RAJYA SABHA" not in "SHRI P.H. PANDIYAN"


# --- the seeded table -------------------------------------------------------

def test_every_emitted_role_code_exists_in_the_schema():
    seeded = set(
        re.findall(r"^\s*\('([a-z_]+)',\s*'(?:presiding|crowd)'", _sql_text(), re.M)
    )
    emitted = {
        code for code, _ in
        [(c, p) for c, p in __import__("debate_fetch")._ROLE_CODES]
    } | {"members_crowd"}
    assert emitted <= seeded, f"parser emits codes the table lacks: {emitted - seeded}"


def test_crowd_is_not_resolvable_and_presiding_is():
    rows = re.findall(
        r"\('([a-z_]+)',\s*'(presiding|crowd)',[^,]+,\s*(TRUE|FALSE)", _sql_text()
    )
    by_code = {c: (kind, flag) for c, kind, flag in rows}
    assert by_code["members_crowd"] == ("crowd", "FALSE")
    for code in ("speaker", "deputy_speaker", "chairman", "deputy_chairman"):
        assert by_code[code] == ("presiding", "TRUE")


def test_no_role_row_carries_a_sansad_id():
    ddl = _sql_without_comments()
    assert "sansad_id" not in ddl
    assert "persons" not in ddl, "speaker_roles must not reference persons"

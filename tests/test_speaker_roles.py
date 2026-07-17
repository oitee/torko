"""Labels that name a role or a crowd rather than a person.

Every case here was drawn from a census of the real corpus (all 64,921
debates), not invented: 131,641 bare role labels, 1,199 crowd labels, 143
distinct role spellings. The spellings pinned below are the ones the corpus
actually prints, with the (loksabha, session, dbslno) they came from noted
where it is useful to go and look.
"""
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
    pathlib.Path(__file__).resolve().parent.parent / "db" / "init" / "06-speaker-roles.sql"
)


def _sql_text() -> str:
    return _SCHEMA.read_text()


def _sql_without_comments() -> str:
    """The DDL with `--` comment lines stripped."""
    return "\n".join(
        line for line in _sql_text().splitlines() if not line.lstrip().startswith("--")
    )


# --- crowd labels -----------------------------------------------------------
# Before these were their own category they fell through to "unresolved",
# conflating "a name we failed to match" with "a label naming nobody at all".

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
    """A label must never be both. The census found zero overlaps in the real
    corpus; this pins that the two vocabularies stay separate."""
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
        # THE ORDERING TRAP. "DEPUTY-SPEAKER" contains "SPEAKER", "DEPUTY-
        # CHAIRMAN" contains "CHAIRMAN", and उपाध्यक्ष contains अध्यक्ष. If the
        # plain forms were tested first, every deputy in the corpus would be
        # filed as their principal -- a different human being, and a
        # misattribution we would have manufactured ourselves.
        ("MR. DEPUTY-SPEAKER", "deputy_speaker"),
        ("उपाध्यक्ष महोदय", "deputy_speaker"),
        # The real corpus form, 58 occurrences in LS13/LS15 -- the OTHER
        # House's officer quoted in a Lok Sabha transcript. LS13/x: see
        # `DEPUTY-CHAIRMAN (RAJYA SABHA):`.
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
    """143 distinct role spellings exist, but they are 3 offices plus noise.
    Searching for the office word absorbs the tail without a rule per typo."""
    assert is_presiding_label(label)
    assert role_code_for_label(label) is not None


def test_a_real_name_is_not_a_role():
    assert role_code_for_label("SHRI SHAILENDRA KUMAR") is None
    assert not is_presiding_label("SHRI SHAILENDRA KUMAR")


def test_deputy_minister_is_not_a_presiding_officer():
    """"Deputy" alone must not trigger: a Deputy Minister is a real person."""
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
    """The invariant this table exists to protect. A role is not a person, so
    it must never be resolved onto one -- `MR. SPEaKER` is five different
    humans across LS13-18."""
    segs = annotate_speakers([_seg("MR. SPEAKER")], [], None)
    assert segs[0]["mpCode"] is None
    assert segs[0]["nameSource"] == "presiding"


# --- a frozen real case -----------------------------------------------------

# Verbatim markup from LS13 / session 9 / dbslno 3795 -- the March 2002 JOINT
# SITTING of both Houses on the Prevention of Terrorism Bill. Because it is a
# joint sitting, the presiding officer is the RAJYA SABHA's Deputy Chairman:
# the other House's chair, appearing in a Lok Sabha transcript. This is the
# only shape in the corpus that produces `deputy_chairman` (58 occurrences),
# and it is why that office exists as its own row rather than being folded
# into `chairman` -- a different human entirely.
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
    """The trap for any future rule that reads a name out of a role label's
    parentheses. `MR. CHAIRMAN (SHRI P.H. PANDIYAN)` names a real human, but
    `DEPUTY-CHAIRMAN (RAJYA SABHA)` names the other House -- reading that as a
    person would invent a member called "Rajya Sabha"."""
    assert role_code_for_label("DEPUTY-CHAIRMAN (RAJYA SABHA)") == "deputy_chairman"
    # Documents the distinction so it cannot be lost silently.
    assert "RAJYA SABHA" not in "SHRI P.H. PANDIYAN"


# --- the seeded table -------------------------------------------------------

def test_every_emitted_role_code_exists_in_the_schema():
    """The parser's slugs and the table's seed rows must not drift apart."""
    seeded = set(
        re.findall(r"^\s*\('([a-z_]+)',\s*'(?:presiding|crowd)'", _sql_text(), re.M)
    )
    emitted = {
        code for code, _ in
        [(c, p) for c, p in __import__("debate_fetch")._ROLE_CODES]
    } | {"members_crowd"}
    assert emitted <= seeded, f"parser emits codes the table lacks: {emitted - seeded}"


def test_crowd_is_not_resolvable_and_presiding_is():
    """The split the whole table exists for: a crowd names nobody forever, a
    presiding officer is a knowable human recoverable from a tenure table."""
    rows = re.findall(
        r"\('([a-z_]+)',\s*'(presiding|crowd)',[^,]+,\s*(TRUE|FALSE)", _sql_text()
    )
    by_code = {c: (kind, flag) for c, kind, flag in rows}
    assert by_code["members_crowd"] == ("crowd", "FALSE")
    for code in ("speaker", "deputy_speaker", "chairman", "deputy_chairman"):
        assert by_code[code] == ("presiding", "TRUE")


def test_no_role_row_carries_a_sansad_id():
    """A role must never be given a person's identifier.

    Checks the DDL only -- the file's comments discuss sansad_id at length
    precisely to explain why the column is absent, so a naive substring search
    over the whole file fails on the prose defending the rule.
    """
    ddl = _sql_without_comments()
    assert "sansad_id" not in ddl
    assert "persons" not in ddl, "speaker_roles must not reference persons"

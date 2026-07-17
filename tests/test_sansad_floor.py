"""
The Sansad floor: every tagged MP is covered, or missing for a NAMED reason.

`scripts/audit_sansad_floor.py` is the only check in this project that asserts a
guarantee rather than reporting a percentage. The guarantee is the floor below
which our dataset would be worse than the source it was built from.

THE MOST IMPORTANT TESTS HERE ARE IN `TestTheGateCanSeeABreach`. A check that
cannot fail is not a check, and this project has shipped three of those (see
internal_docs/023_THE_CENSUS.md §8). Every other test below could pass against
a function that returned `Counter(covered=len(mp_list))` and nothing else.

The first version of this audit was one of those three. It decided "is this MP
printed?" by looking at the labels the PARSER had found -- which made the bug
bucket unreachable: a label that folds to a unique key is matched by the
resolver's own fold table, and a key that is not unique is caught as a
collision. It always passed. The audit now asks the DEBATE TEXT instead, which
is the only reason `test_a_swallowed_turn_is_a_breach` below can go red.

The buckets are a CLOSED SET on purpose. Adding one is a decision about what we
are willing to call an acceptable miss, and it belongs in internal_docs before
it belongs here.
"""
from scripts.audit_sansad_floor import (
    REASON_FOLD_COLLISION,
    REASON_NOT_PRINTED,
    REASON_ROLE_ONLY,
    REASON_UNEXPLAINED,
    audit_debate,
)


def para(label, text="Sir, I rise to speak on this matter before the House."):
    return f"<p><b>{label}:</b> {text}</p>"


def audit(mp_list, *paragraphs):
    return audit_debate(18, 1, 1, "".join(paragraphs), mp_list)


class TestTheFloorHolds:
    def test_a_tagged_mp_who_speaks_is_covered(self):
        mps = [{"mpName": "Shri Kiren Rijiju", "mpCode": 3972, "mpPartCode": 1}]
        reasons, unexplained = audit(mps, para("SHRI KIREN RIJIJU"))
        assert reasons["covered"] == 1
        assert not unexplained

    def test_a_tagged_mp_never_printed_is_not_a_bug(self):
        # Real and common: mpPartDetailList is who PARTICIPATED, which is not
        # who has a speaking turn. LS13/13/6233 ("Papers Laid on the Table")
        # tags 6 MPs and prints 4 -- the other two never appear in the body.
        mps = [
            {"mpName": "Shri Kiren Rijiju", "mpCode": 3972, "mpPartCode": 1},
            {"mpName": "Smt. Bhavna Devraj Chikhalia", "mpCode": 999, "mpPartCode": 2},
        ]
        reasons, unexplained = audit(mps, para("SHRI KIREN RIJIJU"))
        assert reasons["covered"] == 1
        assert reasons[REASON_NOT_PRINTED] == 1
        assert not unexplained

    def test_a_colliding_name_is_a_ceiling_not_a_bug(self):
        # Two tagged people whose names fold to the same key. never-guess drops
        # the label rather than pick, and that is the correct outcome -- so the
        # floor must account for it rather than call it a breach.
        mps = [
            {"mpName": "Shri A. Rajendran", "mpCode": 11, "mpPartCode": 1},
            {"mpName": "Shri B. Rajendran", "mpCode": 22, "mpPartCode": 2},
        ]
        reasons, unexplained = audit(mps, para("SHRI RAJENDRAN"))
        assert reasons[REASON_FOLD_COLLISION] == 2
        assert not unexplained

    def test_an_mp_present_only_as_the_chair_is_accounted_for(self):
        # The office is recorded, the person is not -- deliberately, and worth
        # 131,641 turns corpus-wide. It is a ceiling with a name, not a miss.
        mps = [{"mpName": "Shri Speaker Person", "mpCode": 77, "mpPartCode": 1}]
        reasons, _unexplained = audit(mps, para("MR. SPEAKER"))
        assert reasons[REASON_ROLE_ONLY] + reasons[REASON_NOT_PRINTED] == 1
        assert reasons[REASON_UNEXPLAINED] == 0


class TestTheGateCanSeeABreach:
    """If nothing here can go red, the audit is decoration."""

    def test_a_swallowed_turn_is_a_breach(self):
        # The shape the floor exists to catch. The document plainly prints this
        # MP as the speaker -- name, colon, speech -- but the label is neither
        # bold nor ALL-CAPS, so the splitter opens no turn and the parser is
        # blind to it by construction. Sansad tagged him; we have nothing.
        #
        # This is the test that proves the audit asks the DOCUMENT rather than
        # the parser. Ask the parser and this case is invisible: there is no
        # label for it to report.
        mps = [{"mpName": "Shri Kiren Rijiju", "mpCode": 3972, "mpPartCode": 1}]
        reasons, unexplained = audit_debate(
            18, 1, 1,
            "<p>Shri Kiren Rijiju: Sir, I rise to speak on the matter before us.</p>",
            mps,
        )
        assert reasons[REASON_UNEXPLAINED] == 1
        assert unexplained and unexplained[0][3] == "3972"

    def test_being_talked_about_is_not_speaking(self):
        # The false positive the floor must NOT produce, and the reason it looks
        # for a label POSITION rather than the name anywhere in the text. The
        # Chair naming an MP is not that MP speaking; a body-text check calls
        # this a bug and buries the real ones in noise.
        mps = [{"mpName": "Shri Kiren Rijiju", "mpCode": 3972, "mpPartCode": 1}]
        reasons, unexplained = audit_debate(
            18, 1, 1,
            para("MR. SPEAKER", "The House will now hear Shri Kiren Rijiju on this."),
            mps,
        )
        assert reasons[REASON_UNEXPLAINED] == 0
        assert not unexplained

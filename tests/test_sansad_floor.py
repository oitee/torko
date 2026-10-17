from dashboard_db import (
    REASON_FOLD_COLLISION,
    REASON_NOT_PRINTED,
    REASON_ROLE_ONLY,
    REASON_UNEXPLAINED,
)
from scripts.audit_sansad_floor import audit_debate


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
        # mpPartDetailList lists participants, not speakers.
        # Real case: LS13/13/6233 tags 6 MPs and prints 4.
        mps = [
            {"mpName": "Shri Kiren Rijiju", "mpCode": 3972, "mpPartCode": 1},
            {"mpName": "Smt. Bhavna Devraj Chikhalia", "mpCode": 999, "mpPartCode": 2},
        ]
        reasons, unexplained = audit(mps, para("SHRI KIREN RIJIJU"))
        assert reasons["covered"] == 1
        assert reasons[REASON_NOT_PRINTED] == 1
        assert not unexplained

    def test_a_colliding_name_is_a_ceiling_not_a_bug(self):
        # Two tagged people fold to the same key, so the label is dropped and the floor accounts for it.
        mps = [
            {"mpName": "Shri A. Rajendran", "mpCode": 11, "mpPartCode": 1},
            {"mpName": "Shri B. Rajendran", "mpCode": 22, "mpPartCode": 2},
        ]
        reasons, unexplained = audit(mps, para("SHRI RAJENDRAN"))
        assert reasons[REASON_FOLD_COLLISION] == 2
        assert not unexplained

    def test_an_mp_present_only_as_the_chair_is_accounted_for(self):
        # The office is recorded and the person is not. This is not a miss.
        mps = [{"mpName": "Shri Speaker Person", "mpCode": 77, "mpPartCode": 1}]
        reasons, _unexplained = audit(mps, para("MR. SPEAKER"))
        assert reasons[REASON_ROLE_ONLY] + reasons[REASON_NOT_PRINTED] == 1
        assert reasons[REASON_UNEXPLAINED] == 0


class TestTheGateCanSeeABreach:
    def test_a_swallowed_turn_is_a_breach(self):
        # The document prints this MP as the speaker, but the label is neither bold nor ALL-CAPS.
        # The splitter opens no turn, so the parser cannot see it.
        mps = [{"mpName": "Shri Kiren Rijiju", "mpCode": 3972, "mpPartCode": 1}]
        reasons, unexplained = audit_debate(
            18, 1, 1,
            "<p>Shri Kiren Rijiju: Sir, I rise to speak on the matter before us.</p>",
            mps,
        )
        assert reasons[REASON_UNEXPLAINED] == 1
        assert unexplained and unexplained[0][3] == "3972"

    def test_being_talked_about_is_not_speaking(self):
        # The Chair naming an MP is not that MP speaking, so look for a label position, not body text.
        mps = [{"mpName": "Shri Kiren Rijiju", "mpCode": 3972, "mpPartCode": 1}]
        reasons, unexplained = audit_debate(
            18, 1, 1,
            para("MR. SPEAKER", "The House will now hear Shri Kiren Rijiju on this."),
            mps,
        )
        assert reasons[REASON_UNEXPLAINED] == 0
        assert not unexplained

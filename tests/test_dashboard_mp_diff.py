"""
The per-debate tagged-vs-attributed panel (`dashboard_db.classify_tagged_not_attributed`).

The panel this backs is a demo/trust feature: for one debate, show which MPs
Sansad's own `mpPartDetailList` tagged versus which MPs we attributed a turn
to, in both directions. `internal_docs/027_THE_SANSAD_FLOOR.md` and
`scripts/audit_sansad_floor.py` already established that "tagged but not
attributed" is NOT automatically our failure -- ~14% of tagged MPs are simply
never printed as a speaker at all, a property of the source, not a defect.

`classify_tagged_not_attributed` reuses that script's reason constants and
rebuilds the same three sets it computes (`colliding`, `role_keys`,
`printed_labels`) so the SAME closed-set rule decides "why", not a
reinvention of it. These tests are the DB-shaped mirror of
`tests/test_sansad_floor.py`'s `TestTheFloorHolds` / `TestTheGateCanSeeABreach`
-- same fixtures in spirit, but exercised as "attributed" (DB ground truth)
vs. "tagged", one MP at a time, which is the shape the panel needs and the
aggregate Counter `audit_debate` returns cannot give.

Offline only: no DB, no network. `db_roster.load_db_roster` is called inside
`classify_tagged_not_attributed` but returns `[]` on any connection failure
(see its docstring), so it is a silent no-op here.
"""
from dashboard_db import classify_tagged_not_attributed, get_mp_diff


def para(label, text="Sir, I rise to speak on this matter before the House."):
    return f"<p><b>{label}:</b> {text}</p>"


def classify(mp_list, attributed_codes, *paragraphs):
    return classify_tagged_not_attributed(18, "".join(paragraphs), mp_list, set(attributed_codes))


class TestAgreementAndAddedValue:
    """These two directions never touch classify_tagged_not_attributed at all --
    they're a plain set difference the caller (get_mp_diff) computes directly
    from tagged codes vs. the turns table's attributed codes. Pinned here as
    the contract the frontend panel relies on."""

    def test_tagged_and_attributed_is_agreement_not_a_miss(self):
        mps = [{"mpName": "Shri Kiren Rijiju", "mpCode": 3972, "mpPartCode": 1}]
        out = classify(mps, {"3972"}, para("SHRI KIREN RIJIJU"))
        assert out == []  # nothing to explain: this code is attributed

    def test_attributed_not_tagged_is_not_this_functions_job(self):
        # classify_tagged_not_attributed only ever walks TAGGED mps -- an
        # attributed-but-untagged MP (our added value over the source) simply
        # never appears in its output, by construction.
        mps = [{"mpName": "Shri Kiren Rijiju", "mpCode": 3972, "mpPartCode": 1}]
        out = classify(mps, {"3972", "9999"}, para("SHRI KIREN RIJIJU"))
        assert out == []


class TestReasonsAreHonestNotBlaming:
    def test_never_printed_is_a_source_gap_not_our_fault(self):
        # LS13/13/6233 in miniature: Rijiju is tagged, printed, and attributed
        # (so out of scope for this function); Chikhalia is tagged and never
        # printed in the body at all -- a gap in the source, not in us.
        mps = [
            {"mpName": "Shri Kiren Rijiju", "mpCode": 3972, "mpPartCode": 1},
            {"mpName": "Smt. Bhavna Devraj Chikhalia", "mpCode": 999, "mpPartCode": 2},
        ]
        out = classify(mps, {"3972"}, para("SHRI KIREN RIJIJU"))
        assert out == [
            {"sansadId": "999", "name": "Smt. Bhavna Devraj Chikhalia", "reason": "not_printed"}
        ]

    def test_fold_collision_is_a_ceiling_not_a_bug(self):
        mps = [
            {"mpName": "Shri A. Rajendran", "mpCode": 11, "mpPartCode": 1},
            {"mpName": "Shri B. Rajendran", "mpCode": 22, "mpPartCode": 2},
        ]
        out = classify(mps, set(), para("SHRI RAJENDRAN"))
        reasons = {r["sansadId"]: r["reason"] for r in out}
        assert reasons == {"11": "fold_collision", "22": "fold_collision"}

    def test_role_only_is_accounted_for(self):
        mps = [{"mpName": "Shri Speaker Person", "mpCode": 77, "mpPartCode": 1}]
        out = classify(mps, set(), para("MR. SPEAKER"))
        assert out[0]["reason"] in ("role_only", "not_printed")

    def test_a_swallowed_turn_is_genuinely_unexplained(self):
        # The MP is printed as a speaker in the raw text, their key names
        # nobody else, and yet no turn is attributed to them -- the one
        # bucket that is a real, nameable miss.
        mps = [{"mpName": "Shri Kiren Rijiju", "mpCode": 3972, "mpPartCode": 1}]
        out = classify(mps, set(), para("SHRI KIREN RIJIJU"))
        assert out == [
            {"sansadId": "3972", "name": "Shri Kiren Rijiju", "reason": "unexplained"}
        ]


class TestGetMpDiffHandlesTheEmptyCase:
    def test_no_debate_returns_none(self, monkeypatch):
        class FakeConn:
            def execute(self, *a, **k):
                class R:
                    def fetchone(self_inner):
                        return None

                return R()

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        class FakeEngine:
            def connect(self):
                return FakeConn()

        monkeypatch.setattr("dashboard_db.get_engine", lambda: FakeEngine())
        assert get_mp_diff(18, 1, 999999) is None

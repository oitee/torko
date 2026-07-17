from dashboard_db import classify_tagged_not_attributed, get_mp_diff


def para(label, text="Sir, I rise to speak on this matter before the House."):
    return f"<p><b>{label}:</b> {text}</p>"


def classify(mp_list, attributed_codes, *paragraphs):
    return classify_tagged_not_attributed(18, "".join(paragraphs), mp_list, set(attributed_codes))


class TestAgreementAndAddedValue:
    def test_tagged_and_attributed_is_agreement_not_a_miss(self):
        mps = [{"mpName": "Shri Kiren Rijiju", "mpCode": 3972, "mpPartCode": 1}]
        out = classify(mps, {"3972"}, para("SHRI KIREN RIJIJU"))
        assert out == []  # nothing to explain: this code is attributed

    def test_attributed_not_tagged_is_not_this_functions_job(self):
        # Attributed but untagged MPs never appear in the output.
        mps = [{"mpName": "Shri Kiren Rijiju", "mpCode": 3972, "mpPartCode": 1}]
        out = classify(mps, {"3972", "9999"}, para("SHRI KIREN RIJIJU"))
        assert out == []


class TestReasonsAreHonestNotBlaming:
    def test_never_printed_is_a_source_gap_not_our_fault(self):
        # Real case: LS13/13/6233. Rijiju is tagged and attributed. Chikhalia is tagged and never printed in the body.
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
        # The MP is printed as a speaker in the raw text, but no turn is attributed to the MP.
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

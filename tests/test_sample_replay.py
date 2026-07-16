"""
Replaying a fixed set of debates through the sampler.

The sansad.in API is unreliable, so these tests never hit the network: they
monkeypatch `debate_fetch.fetch_debate` to return canned debate payloads and let
the real parser run over them. This exercises the whole
fetch -> parse -> classify path and pins down how many speakers stay unverified.

The count acts as a regression baseline: an improvement to normalisation should
keep the number of unverified speakers at or below BASELINE_UNVERIFIED — never
above it. Bring the baseline down when a change genuinely resolves more speakers.
"""
import random
import sys

import pytest

import debate_fetch
import sample_unverified

# One anchored member (later turns unanchored under the same name), plus a
# presiding officer who is nobody on the roster.
_DEBATE_HTML = (
    '<p><b><a name="500*2"></a>SHRI NEW MEMBER:</b> Opening remarks.</p>'
    "<p><b>SHRI NEW MEMBER:</b> A follow-up point.</p>"
    "<p><b>MR. SPEAKER:</b> Order, order.</p>"
)

# Keyed by (loksabha, session, dbSlno) — what fetch_debate would return.
_PAYLOADS = {
    (15, 1, 1001): {"debateDesc": _DEBATE_HTML, "mpPartDetailList": []},
    (16, 2, 2002): {"debateDesc": _DEBATE_HTML, "mpPartDetailList": []},
}

# Two debates: the member resolves by anchor-reuse and MR. SPEAKER is now
# presiding-tagged by the parser, so nothing is left unverified.
BASELINE_UNVERIFIED = 0


@pytest.fixture(autouse=True)
def no_db(monkeypatch):
    """Keep every test in this file off Postgres.

    The sampler loads a DB roster per term to back the parser's last-resort
    "name-db" tier. Tests must never touch a real database, so the loader is
    stubbed to the same empty list it returns when Postgres is down, and the
    per-run cache is cleared so module-level state cannot leak between tests.
    """
    sample_unverified._DB_ROSTER_CACHE.clear()
    monkeypatch.setattr(sample_unverified, "load_db_roster", lambda term: [])
    yield
    sample_unverified._DB_ROSTER_CACHE.clear()


@pytest.fixture
def fake_api(monkeypatch):
    """Serve canned payloads and skip the polite request delay."""
    def fake_fetch(ls, session, db_slno):
        return _PAYLOADS[(ls, session, db_slno)]

    monkeypatch.setattr(debate_fetch, "fetch_debate", fake_fetch)
    monkeypatch.setattr(sample_unverified.time, "sleep", lambda *a, **k: None)


REFS = [
    {"loksabha": 15, "session": 1, "dbSlno": 1001, "era": "modern"},
    {"loksabha": 16, "session": 2, "dbSlno": 2002, "era": "modern"},
]


class TestCollectRefs:
    def test_unverified_count_does_not_exceed_baseline(self, fake_api):
        examples, _, _, _, _, _ = sample_unverified.collect_refs(REFS)
        assert len(examples) <= BASELINE_UNVERIFIED

    def test_presiding_officer_is_not_an_unverified_example(self, fake_api):
        # "SHRI NEW MEMBER" resolves via anchor-reuse; "MR. SPEAKER" is
        # presiding-tagged by the parser, so no unverified examples remain.
        examples, _, _, _, _, _ = sample_unverified.collect_refs(REFS)
        assert examples == []

    def test_presiding_officers_are_classified(self, fake_api):
        _, _, _, presiding, _, _ = sample_unverified.collect_refs(REFS)
        assert len(presiding) == 2
        for row in presiding:
            assert row["speaker"] == "MR. SPEAKER"
            assert row["turns"] == 1

    def test_debates_with_only_presiding_left_count_as_clean(self, fake_api):
        _, clean_debates, _, _, _, _ = sample_unverified.collect_refs(REFS)
        assert len(clean_debates) == 2

    def test_resolved_speakers_are_recorded_per_debate(self, fake_api):
        # "SHRI NEW MEMBER" is anchored once and reused once -> one resolved
        # row per debate, covering both turns, with both name sources noted.
        _, _, resolved, _, _, _ = sample_unverified.collect_refs(REFS)
        assert len(resolved) == 2  # one row per debate for mpCode 500
        for row in resolved:
            assert row["mp_code"] == "500"
            assert row["turns"] == 2
            assert row["name_sources"] == ["anchor", "anchor-reuse"]


class TestDbRosterIsWiredIn:
    """The sampler is our only regression gate, so it must exercise the
    parser's "name-db" tier rather than being blind to it.
    """

    def test_passes_the_terms_db_roster_through_to_the_parser(
        self, fake_api, monkeypatch
    ):
        seen: list = []

        def spy(payload, db_roster=None):
            seen.append(db_roster)
            return []

        monkeypatch.setattr(
            sample_unverified, "load_db_roster", lambda term: [{"mpCode": term, "mpName": "X"}]
        )
        monkeypatch.setattr(sample_unverified, "parse_segments", spy)
        sample_unverified.collect_refs(REFS)

        # one roster per debate, each scoped to that debate's own term
        assert seen == [[{"mpCode": 15, "mpName": "X"}], [{"mpCode": 16, "mpName": "X"}]]

    def test_a_db_roster_never_costs_an_anchored_resolution(self, fake_api, monkeypatch):
        # End-to-end through the real parser: the DB roster names this debate's
        # speaker under a *different* code (777) than the anchor printed in the
        # transcript (500). The anchor must still win, and the second turn must
        # still reach 500 by anchor-reuse — handing the sampler a roster may
        # never change or cost an attribution it already made.
        monkeypatch.setattr(
            sample_unverified,
            "load_db_roster",
            lambda term: [{"mpCode": "777", "mpName": "Shri New Member"}],
        )
        _, _, resolved, _, _, _ = sample_unverified.collect_refs(REFS)
        assert [r["mp_code"] for r in resolved] == ["500", "500"]
        for row in resolved:
            assert row["turns"] == 2
            assert row["name_sources"] == ["anchor", "anchor-reuse"]

    def test_roster_is_loaded_once_per_term_not_once_per_debate(self, fake_api, monkeypatch):
        calls: list[int] = []

        def counting_loader(term):
            calls.append(term)
            return []

        monkeypatch.setattr(sample_unverified, "load_db_roster", counting_loader)
        # four debates across two terms -> two loads, not four
        refs = REFS + [dict(r, dbSlno=r["dbSlno"]) for r in REFS]
        sample_unverified.collect_refs(refs)
        assert calls == [15, 16]

    def test_sampler_runs_unchanged_with_no_postgres(self, fake_api, monkeypatch):
        # load_db_roster swallows a dead DB into []; the tier must then no-op
        # and leave the sampler's output exactly as the no_db baseline.
        monkeypatch.setattr(sample_unverified, "load_db_roster", lambda term: [])
        examples, clean, resolved, presiding, _, _ = sample_unverified.collect_refs(REFS)
        assert examples == []
        assert len(clean) == 2
        assert len(resolved) == 2
        assert len(presiding) == 2


class TestDefaultOutPath:
    def test_is_a_timestamped_run_file_in_the_default_dir(self):
        from datetime import datetime

        path = sample_unverified.default_out_path(datetime(2026, 7, 15, 14, 30, 5))
        assert path == sample_unverified.DEFAULT_OUT_DIR / "20260715_143005_unverified_run.md"

    def test_distinct_timestamps_yield_distinct_files(self):
        from datetime import datetime

        a = sample_unverified.default_out_path(datetime(2026, 7, 15, 14, 30, 5))
        b = sample_unverified.default_out_path(datetime(2026, 7, 15, 14, 30, 6))
        assert a != b


def _example(**overrides):
    ex = {
        "loksabha": 15, "session": 1, "dbSlno": 1001, "era": "modern",
        "debate_type": None, "debate_date": None,
        "speaker_raw": "MR. SPEAKER", "speaker": "MR. SPEAKER",
        "name_source": "unresolved", "category": "presiding_officer",
        "text_excerpt": "Order.", "url": "https://example/x",
    }
    ex.update(overrides)
    return ex


class TestWriteOutputs:
    def test_writes_to_the_given_paths_and_creates_parent_dir(self, tmp_path):
        out_md = tmp_path / "nested" / "20260715_143005_unverified_run.md"
        out_jsonl = out_md.with_suffix(".jsonl")
        sample_unverified.write_outputs(
            out_md, out_jsonl, "2026-07-15 14:30:05", [_example()], clean_debates=[]
        )

        assert out_md.exists()
        assert out_jsonl.exists()
        text = out_md.read_text(encoding="utf-8")
        assert "MR. SPEAKER" in text
        assert "2026-07-15 14:30:05" in text  # the canonical stamp is in the file

    def test_writes_resolved_rows_and_baseline_section_when_given(self, tmp_path):
        out_md = tmp_path / "run.md"
        out_jsonl = out_md.with_suffix(".jsonl")
        resolved_row = {
            "loksabha": 15, "session": 1, "dbSlno": 1001, "era": "modern",
            "mp_code": "500", "mp_name": "Shri New Member",
            "speaker_raw": "SHRI NEW MEMBER",
            "name_sources": ["anchor", "anchor-reuse"], "turns": 2,
        }
        sample_unverified.write_outputs(
            out_md, out_jsonl, "2026-07-15 14:30:05", [_example()],
            clean_debates=[], resolved=[resolved_row],
        )

        out_resolved = tmp_path / "run_resolved.jsonl"
        assert out_resolved.exists()
        assert '"mp_code": "500"' in out_resolved.read_text(encoding="utf-8")
        text = out_md.read_text(encoding="utf-8")
        assert "Resolved speakers (regression baseline)" in text
        assert "| anchor | 1 |" in text

    def test_writes_presiding_rows_and_section_when_given(self, tmp_path):
        out_md = tmp_path / "run.md"
        out_jsonl = out_md.with_suffix(".jsonl")
        presiding_row = {
            "loksabha": 15, "session": 1, "dbSlno": 1001, "era": "modern",
            "speaker": "MR. SPEAKER", "turns": 3,
            "url": "https://example/x",
        }
        sample_unverified.write_outputs(
            out_md, out_jsonl, "2026-07-15 14:30:05", [],
            clean_debates=[], presiding=[presiding_row],
        )

        out_presiding = tmp_path / "run_presiding.jsonl"
        assert out_presiding.exists()
        assert "MR. SPEAKER" in out_presiding.read_text(encoding="utf-8")
        text = out_md.read_text(encoding="utf-8")
        assert "Presiding officers (classified)" in text
        assert "1 chair rows (one per debate + label), 1 distinct labels" in text

    def test_untagged_chair_label_still_surfaces_as_leakage(self, tmp_path):
        # The parser tags genuine chair labels, so anything the SAMPLER's own
        # PRESIDING_RE still catches among the examples is a gap in
        # is_presiding_label — the leakage signal the category now carries.
        out_md = tmp_path / "run.md"
        leak = _example(speaker="THE PANEL OF CHAIRMEN CONVENOR",
                        category=sample_unverified.classify("THE PANEL OF CHAIRMEN CONVENOR"))
        assert leak["category"] == "presiding_officer"
        sample_unverified.write_outputs(
            out_md, out_md.with_suffix(".jsonl"), "2026-07-15 14:30:05", [leak],
            clean_debates=[], presiding=[],
        )
        text = out_md.read_text(encoding="utf-8")
        assert "| presiding_officer | 1 |" in text

    def test_refuses_to_overwrite_an_existing_run_file(self, tmp_path):
        out_md = tmp_path / "run.md"
        out_jsonl = out_md.with_suffix(".jsonl")
        out_md.write_text("already here\n", encoding="utf-8")
        with pytest.raises(SystemExit):
            sample_unverified.write_outputs(
                out_md, out_jsonl, "2026-07-15 14:30:05", [_example()], clean_debates=[]
            )


class TestSwallowedLabels:
    """The denominator check: labels sitting inside another speaker's turn.

    These are turns the splitter never opened. Every other count the sampler
    reports is computed over labels the splitter *found*, so nothing else can
    see them -- which is exactly why this probe reads the splitter's output
    rather than restating its boundary rules.
    """

    def test_finds_a_label_buried_in_another_turn(self):
        segments = [
            {
                "speakerLabel": "श्री प्रियरंजन दासमुंशी",
                "text": "पांच-दस मिनट बढ़ जाएं तो कोई बात नहीं।\n\n"
                "SHRI E. PONNUSWAMY: Madam, she has not even mentioned a single point.\n\n"
                "MADAM CHAIRMAN: Mr. Ponnuswamy, you can speak during your turn.",
            }
        ]
        assert sample_unverified.swallowed_labels(segments) == [
            "SHRI E. PONNUSWAMY",
            "MADAM CHAIRMAN",
        ]

    def test_counts_every_occurrence_not_distinct_labels(self):
        segments = [
            {"speakerLabel": "X", "text": "MADAM CHAIRMAN: One.\n\nMADAM CHAIRMAN: Two."}
        ]
        assert sample_unverified.swallowed_labels(segments) == [
            "MADAM CHAIRMAN",
            "MADAM CHAIRMAN",
        ]

    def test_a_cleanly_split_debate_reports_nothing(self):
        # each speaker's label is the segment's own label, never in its body
        segments = [
            {"speakerLabel": "SHRI E. PONNUSWAMY", "text": "Madam, she has not."},
            {"speakerLabel": "MADAM CHAIRMAN", "text": "You can speak in your turn."},
        ]
        assert sample_unverified.swallowed_labels(segments) == []

    def test_ordinary_prose_with_a_colon_is_not_a_label(self):
        segments = [
            {
                "speakerLabel": "X",
                "text": "I want to say this: the Bill is good.\n\n… ( Interruptions )",
            }
        ]
        assert sample_unverified.swallowed_labels(segments) == []

    def test_devanagari_labels_are_a_known_blind_spot(self):
        # _is_caps_label keys on the absence of lowercase *ASCII*, so a
        # Devanagari label would match everything and mean nothing. The probe
        # only claims a lower bound; this pins that limit rather than hiding it.
        segments = [{"speakerLabel": "X", "text": "सभापति महोदया : कृपया समाप्त करें।"}]
        assert sample_unverified.swallowed_labels(segments) == []

    def test_a_colon_beyond_the_label_window_is_ignored(self):
        segments = [
            {"speakerLabel": "X", "text": "A" * 250 + ": trailing colon, far too late"}
        ]
        assert sample_unverified.swallowed_labels(segments) == []


# Raw, undecoded labels pulled from LS14/5/2711 -- the debate credited 303
# turns to Shri Mohan Singh before 5f9bd3c. Each strips to zero usable whole
# words under debate_fetch._name_parts: three are CDAC legacy-font gibberish
# (only single-letter "initials" survive folding) and the fourth is an Urdu
# label that transliteration cannot turn into Latin word tokens at all.
REAL_UNREADABLE_LABELS = [
    "gÉÉÒ àÉÉäcxÉ ÉËºÉc (nä´ÉÉÊ®ªÉÉ)",
    "gÉÉÒ xÉÉÒiÉÉÒ¶É BÉÖEàÉÉ®",
    "+ÉvªÉFÉ àÉcÉänªÉ",
    "جناب اسدالدین اویسی ( حیدرآباد )",
]


class TestUnfoundedAttributions:
    """The misattribution guard: no anchor-reuse mpCode may rest on a label
    that names nobody.

    `reuse_anchors` mints "anchor-reuse" purely from comparing one label
    against another (`labels_name_same_person`). If a label strips to zero
    usable whole words, the comparison had nothing to compare -- which is
    exactly what happened in 5f9bd3c, when a name-comparison bug read "no
    evidence" as "same person" and stamped one name across 303 turns. This
    class pins that this cannot happen invisibly again.
    """

    def test_flags_real_unreadable_labels_that_drove_the_original_bug(self):
        segments = [
            {"speakerLabel": label, "nameSource": "anchor-reuse", "mpCode": "9999"}
            for label in REAL_UNREADABLE_LABELS
        ]
        assert sample_unverified.unfounded_attributions(segments) == REAL_UNREADABLE_LABELS

    def test_a_readable_anchor_reuse_label_is_not_flagged(self):
        segments = [
            {"speakerLabel": "SHRI E. PONNUSWAMY", "nameSource": "anchor-reuse", "mpCode": "500"}
        ]
        assert sample_unverified.unfounded_attributions(segments) == []

    def test_anchor_is_exempt_even_with_the_same_unreadable_label(self):
        # An anchor's mpCode came from the source's own ID tag, not from a
        # name comparison, so an unreadable label on an "anchor" segment is
        # not this bug -- only "anchor-reuse" is in scope.
        segments = [
            {
                "speakerLabel": REAL_UNREADABLE_LABELS[0],
                "nameSource": "anchor",
                "mpCode": "500",
            }
        ]
        assert sample_unverified.unfounded_attributions(segments) == []

    def test_accepted_blind_spot_other_name_sources_are_out_of_scope(self):
        # This probe only ever looks at "anchor-reuse". A foundation-less
        # match minted under any other nameSource tag -- here name-translit,
        # which decodes/transliterates internally before matching, so a raw
        # label with zero _name_parts is not evidence of a bad match there --
        # is structurally invisible to this check. Pinned deliberately rather
        # than hidden: if this exact class of bug ever appears under a
        # different nameSource, this probe will not catch it.
        segments = [
            {
                "speakerLabel": REAL_UNREADABLE_LABELS[0],
                "nameSource": "name-translit",
                "mpCode": "500",
            }
        ]
        assert sample_unverified.unfounded_attributions(segments) == []

    def test_counts_every_occurrence_not_distinct_labels(self):
        segments = [
            {"speakerLabel": REAL_UNREADABLE_LABELS[0], "nameSource": "anchor-reuse", "mpCode": "1"},
            {"speakerLabel": REAL_UNREADABLE_LABELS[0], "nameSource": "anchor-reuse", "mpCode": "1"},
        ]
        assert sample_unverified.unfounded_attributions(segments) == [
            REAL_UNREADABLE_LABELS[0],
            REAL_UNREADABLE_LABELS[0],
        ]

    def test_reproduces_the_original_bug_end_to_end_via_reuse_anchors(self, monkeypatch):
        # Simulates the exact mechanism behind 5f9bd3c: an anchored turn with
        # an unreadable (legacy-gibberish) label, followed by an unresolved
        # turn under the *same* unreadable label. Under the lenient
        # pre-5f9bd3c comparison (both directions merely "not False", so "no
        # evidence" reads as "same person"), reuse_anchors wrongly claims the
        # second turn -- and this probe catches it. Under the real, current
        # comparison, the claim never happens and the probe reports nothing.
        label = REAL_UNREADABLE_LABELS[0]
        segments = [
            {"speakerLabel": label, "mpCode": "500", "mpName": "Shri Mohan Singh", "nameSource": "anchor"},
            {"speakerLabel": label, "mpCode": None, "nameSource": "unresolved"},
        ]

        def lenient(a, b):
            return (
                debate_fetch._name_agreement(a, b) is not False
                and debate_fetch._name_agreement(b, a) is not False
            )

        monkeypatch.setattr(debate_fetch, "labels_name_same_person", lenient)
        debate_fetch.reuse_anchors(segments)
        assert segments[1]["nameSource"] == "anchor-reuse"
        assert sample_unverified.unfounded_attributions(segments) == [label]

    def test_the_real_fixed_comparison_never_reproduces_the_bug(self):
        # Same setup, no monkeypatch: the strict, currently-shipped
        # `labels_name_same_person` refuses to match on "no evidence", so the
        # second turn stays unresolved and the probe finds nothing to flag.
        label = REAL_UNREADABLE_LABELS[0]
        segments = [
            {"speakerLabel": label, "mpCode": "500", "mpName": "Shri Mohan Singh", "nameSource": "anchor"},
            {"speakerLabel": label, "mpCode": None, "nameSource": "unresolved"},
        ]
        debate_fetch.reuse_anchors(segments)
        assert segments[1]["nameSource"] == "unresolved"
        assert sample_unverified.unfounded_attributions(segments) == []


class TestSplitCounts:
    def test_splits_sum_to_n(self):
        assert sample_unverified.split_counts(10, 0.67) == (7, 3)

    def test_rounds_the_legacy_share(self):
        # 100 * 0.67 = 67.0 exactly; no rounding surprises here
        assert sample_unverified.split_counts(100, 0.67) == (67, 33)


class TestSampleDebateRefs:
    """Drawing a fixed number of debates, era-split, with no fetching/parsing."""

    def _fake_search(self, monkeypatch, per_ls_records):
        """Stub random_debate_refs to hand back a fresh slice of canned records
        per loksabha on each call -- real `random_debate_refs` draws a random
        page each time, so a stub returning the same first-k every call would
        make every debate after the first k look already-visited and starve
        the draw loop."""
        queues = {ls: list(records) for ls, records in per_ls_records.items()}

        def fake(loksabha, k):
            batch = queues[loksabha][:k]
            queues[loksabha] = queues[loksabha][k:] + batch
            return batch

        monkeypatch.setattr(sample_unverified, "random_debate_refs", fake)

    def test_draws_n_debates_split_by_era(self, monkeypatch):
        random.seed(1)
        per_ls = {
            13: [{"loksabha": 13, "session": 1, "dbSlno": i} for i in range(1, 20)],
            14: [{"loksabha": 14, "session": 1, "dbSlno": i} for i in range(20, 40)],
            15: [{"loksabha": 15, "session": 1, "dbSlno": i} for i in range(40, 60)],
            16: [{"loksabha": 16, "session": 1, "dbSlno": i} for i in range(60, 80)],
            17: [{"loksabha": 17, "session": 1, "dbSlno": i} for i in range(80, 100)],
            18: [{"loksabha": 18, "session": 1, "dbSlno": i} for i in range(100, 120)],
        }
        self._fake_search(monkeypatch, per_ls)

        refs = sample_unverified.sample_debate_refs(10, 0.67)

        assert len(refs) == 10
        n_legacy = sum(1 for r in refs if r["era"] == "legacy")
        n_modern = sum(1 for r in refs if r["era"] == "modern")
        assert (n_legacy, n_modern) == (7, 3)
        # no duplicate debates within the drawn set
        keys = [(r["loksabha"], r["session"], r["dbSlno"]) for r in refs]
        assert len(keys) == len(set(keys))

    def test_excludes_given_keys(self, monkeypatch):
        random.seed(1)
        per_ls = {
            13: [{"loksabha": 13, "session": 1, "dbSlno": i} for i in range(1, 5)],
            14: [{"loksabha": 14, "session": 1, "dbSlno": i} for i in range(20, 24)],
            15: [{"loksabha": 15, "session": 1, "dbSlno": i} for i in range(40, 44)],
            16: [{"loksabha": 16, "session": 1, "dbSlno": i} for i in range(60, 64)],
            17: [{"loksabha": 17, "session": 1, "dbSlno": i} for i in range(80, 84)],
            18: [{"loksabha": 18, "session": 1, "dbSlno": i} for i in range(100, 104)],
        }
        self._fake_search(monkeypatch, per_ls)
        exclude = {(13, 1, 1), (13, 1, 2), (13, 1, 3)}

        refs = sample_unverified.sample_debate_refs(4, 1.0, exclude=exclude)

        keys = {(r["loksabha"], r["session"], r["dbSlno"]) for r in refs}
        assert keys.isdisjoint(exclude)
        assert len(refs) == 4


class TestMainCliWiring:
    """`main()`'s argument handling, with collect/collect_refs/write_outputs
    stubbed out so these stay unit tests, not end-to-end runs."""

    def _stub_everything(self, monkeypatch, calls):
        monkeypatch.setattr(
            sample_unverified, "collect",
            lambda target: (calls.setdefault("collect_target", target), [], [], [], [], [], [])[1:],
        )
        monkeypatch.setattr(
            sample_unverified, "collect_refs",
            lambda refs: (calls.setdefault("collect_refs_refs", refs), [], [], [], [], [], [])[1:],
        )
        monkeypatch.setattr(sample_unverified, "write_outputs", lambda *a, **k: None)

    def test_target_mode_defaults_to_100_and_calls_collect(self, monkeypatch, tmp_path):
        calls: dict = {}
        self._stub_everything(monkeypatch, calls)
        monkeypatch.setattr(
            sys, "argv", ["sample_unverified", "--out", str(tmp_path / "run.md")]
        )
        sample_unverified.main()
        assert calls["collect_target"] == 100

    def test_target_flag_is_passed_through_unchanged(self, monkeypatch, tmp_path):
        calls: dict = {}
        self._stub_everything(monkeypatch, calls)
        monkeypatch.setattr(
            sys, "argv",
            ["sample_unverified", "--target", "5", "--out", str(tmp_path / "run.md")],
        )
        sample_unverified.main()
        assert calls["collect_target"] == 5

    def test_target_and_debates_are_mutually_exclusive(self, monkeypatch, tmp_path):
        monkeypatch.setattr(
            sys, "argv",
            ["sample_unverified", "--target", "5", "--debates", "3",
             "--out", str(tmp_path / "run.md")],
        )
        with pytest.raises(SystemExit):
            sample_unverified.main()

    def test_include_file_without_debates_is_rejected(self, monkeypatch, tmp_path):
        monkeypatch.setattr(
            sys, "argv",
            ["sample_unverified", "--include-file", "internal_docs/008_UNVERIFIED_SPEAKERS_SAMPLE.md",
             "--out", str(tmp_path / "run.md")],
        )
        with pytest.raises(SystemExit):
            sample_unverified.main()

    def test_debates_mode_draws_and_dedupes_against_include_file(self, monkeypatch, tmp_path):
        calls: dict = {}
        self._stub_everything(monkeypatch, calls)
        seed_refs = [
            {"loksabha": 13, "session": 13, "dbSlno": 5789, "era": "legacy"},
            {"loksabha": 15, "session": 10, "dbSlno": 6531, "era": "modern"},
        ]
        monkeypatch.setattr(sample_unverified, "refs_from_file", lambda path: seed_refs)
        drawn = [
            {"loksabha": 13, "session": 13, "dbSlno": 5789, "era": "legacy"},  # dup of seed
            {"loksabha": 14, "session": 1, "dbSlno": 999, "era": "legacy"},
        ]
        monkeypatch.setattr(
            sample_unverified, "sample_debate_refs",
            lambda n, frac, exclude=None: drawn,
        )
        monkeypatch.setattr(
            sys, "argv",
            ["sample_unverified", "--debates", "2", "--include-file", "some_run.md",
             "--out", str(tmp_path / "run.md")],
        )
        sample_unverified.main()
        refs = calls["collect_refs_refs"]
        # seed_refs are kept in full (the stub is what dedupes against them via
        # `exclude`, exercised separately by TestSampleDebateRefs), plus the
        # freshly drawn refs alongside them
        assert refs == seed_refs + drawn

    def test_dry_run_does_not_call_collect_refs(self, monkeypatch, tmp_path, capsys):
        calls: dict = {}
        self._stub_everything(monkeypatch, calls)
        monkeypatch.setattr(sample_unverified, "refs_from_file", lambda path: [])
        monkeypatch.setattr(
            sample_unverified, "sample_debate_refs",
            lambda n, frac, exclude=None: [
                {"loksabha": 13, "session": 1, "dbSlno": 1, "era": "legacy"},
            ],
        )
        monkeypatch.setattr(
            sys, "argv",
            ["sample_unverified", "--debates", "1", "--dry-run",
             "--out", str(tmp_path / "run.md")],
        )
        sample_unverified.main()
        assert "collect_refs_refs" not in calls
        out = capsys.readouterr().out
        assert "13/1/1" in out


class TestRefsFromFile:
    """Reading the debate links back out of a prior run file."""

    def test_extracts_unique_debate_refs(self, tmp_path):
        run_file = tmp_path / "20260714_120030_unverified_run.md"
        run_file.write_text(
            "[view](https://sansad.in/ls/debates/view-debate?ls=15&session=1&dbslno=1001)\n"
            "[view](https://sansad.in/ls/debates/view-debate?ls=15&session=1&dbslno=1001)\n"
            "[view](https://sansad.in/ls/debates/view-debate?ls=16&session=2&dbslno=2002)\n",
            encoding="utf-8",
        )

        refs = sample_unverified.refs_from_file(run_file)
        assert refs == [
            {"loksabha": 15, "session": 1, "dbSlno": 1001, "era": "modern"},
            {"loksabha": 16, "session": 2, "dbSlno": 2002, "era": "modern"},
        ]

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(SystemExit):
            sample_unverified.refs_from_file(tmp_path / "nope.md")

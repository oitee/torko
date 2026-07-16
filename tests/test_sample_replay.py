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
        examples, _, _, _ = sample_unverified.collect_refs(REFS)
        assert len(examples) <= BASELINE_UNVERIFIED

    def test_presiding_officer_is_not_an_unverified_example(self, fake_api):
        # "SHRI NEW MEMBER" resolves via anchor-reuse; "MR. SPEAKER" is
        # presiding-tagged by the parser, so no unverified examples remain.
        examples, _, _, _ = sample_unverified.collect_refs(REFS)
        assert examples == []

    def test_presiding_officers_are_classified(self, fake_api):
        _, _, _, presiding = sample_unverified.collect_refs(REFS)
        assert len(presiding) == 2
        for row in presiding:
            assert row["speaker"] == "MR. SPEAKER"
            assert row["turns"] == 1

    def test_debates_with_only_presiding_left_count_as_clean(self, fake_api):
        _, clean_debates, _, _ = sample_unverified.collect_refs(REFS)
        assert len(clean_debates) == 2

    def test_resolved_speakers_are_recorded_per_debate(self, fake_api):
        # "SHRI NEW MEMBER" is anchored once and reused once -> one resolved
        # row per debate, covering both turns, with both name sources noted.
        _, _, resolved, _ = sample_unverified.collect_refs(REFS)
        assert len(resolved) == 2  # one row per debate for mpCode 500
        for row in resolved:
            assert row["mp_code"] == "500"
            assert row["turns"] == 2
            assert row["name_sources"] == ["anchor", "anchor-reuse"]


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

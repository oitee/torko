"""
Reading a debate out of the corpus instead of off the wire.

These tests are offline and need no Postgres: the DB round-trip itself is not
what can hurt us. Two other things are.

The first is the payload SHAPE. `debate_store` promises the parsers cannot tell
a corpus read from an API read, and every parser downstream believes that
promise silently -- there is no assertion anywhere in `debate_fetch` that
`mpPartDetailList` holds ints or that `debateDate` looks like "14/12/2024". If
the corpus hands back a `date` object or a str mpCode, nothing raises; the
parser just quietly behaves differently depending on where the debate came
from. Both fixtures below were checked against a live call to LS18/3/1758.

The second is the FALLBACK. `load_debate`'s whole point is that "db" is loud
and "auto" is quiet, so a bulk caller cannot silently drop back to 64,921 HTTP
requests (internal_docs/025_THE_OPEN_ITEMS.md item 2). That is a claim about
what happens on failure, which is exactly the kind of claim that rots without
a test.
"""
from datetime import date
from types import SimpleNamespace
from unittest.mock import patch

import pytest

import debate_fetch
import debate_store
from debate_store import _row_to_payload, load_debate

# One `debates` row, trimmed. mp_list_raw is what JSONB actually returns:
# already parsed, mpCode still an int.
ROW = SimpleNamespace(
    raw_html="<p><b>SHRI KIREN RIJIJU:</b> Sir, I rise to speak.</p>",
    mp_list_raw=[{"mpName": "Shri Kiren Rijiju", "mpCode": 3972, "mpPartCode": 1}],
    debate_date=date(2024, 12, 14),
    debate_type="SPECIAL DISCUSSION",
    contents="14-12-2024 Discussion on the Constitution",
)


class TestPayloadShape:
    def test_maps_the_five_keys_the_parsers_read(self):
        payload = _row_to_payload(ROW)
        assert payload["debateDesc"] == ROW.raw_html
        assert payload["mpPartDetailList"] == ROW.mp_list_raw
        assert payload["debateType"] == "SPECIAL DISCUSSION"
        assert payload["contents"] == ROW.contents

    def test_date_goes_back_into_the_api_s_own_format(self):
        # The API sends "14/12/2024"; the table holds a real DATE. Handing back
        # a date object would give callers a different type depending on where
        # the debate came from.
        assert _row_to_payload(ROW)["debateDate"] == "14/12/2024"

    def test_mpcode_stays_an_int(self):
        # resolve_speaker compares mpCodes for identity. An int/str drift here
        # splits one person into two and nothing raises.
        code = _row_to_payload(ROW)["mpPartDetailList"][0]["mpCode"]
        assert isinstance(code, int)

    def test_missing_member_list_reads_as_empty_not_none(self):
        # build_speaker_index iterates this. None would raise far from here.
        row = SimpleNamespace(**{**ROW.__dict__, "mp_list_raw": None})
        assert _row_to_payload(row)["mpPartDetailList"] == []

    def test_missing_date_is_none_rather_than_a_crash(self):
        row = SimpleNamespace(**{**ROW.__dict__, "debate_date": None})
        assert _row_to_payload(row)["debateDate"] is None

    def test_the_corpus_payload_parses_exactly_like_an_api_payload(self):
        # The promise in one line: hand the reconstructed payload to the parser
        # and it resolves the speaker, with no API in sight.
        payload = _row_to_payload(ROW)
        segments = debate_fetch.split_by_speaker(
            payload["debateDesc"], payload["mpPartDetailList"]
        )
        assert [s["mpName"] for s in segments] == ["Shri Kiren Rijiju"]


class TestSourceSelection:
    def test_api_source_never_touches_the_corpus(self):
        with patch.object(debate_fetch, "fetch_debate", return_value={"debateDesc": "x"}) as wire:
            with patch.object(debate_store, "load_debate", side_effect=AssertionError("read the DB")):
                assert debate_fetch.load_debate(18, 3, 1758, source="api") == {"debateDesc": "x"}
        wire.assert_called_once_with(18, 3, 1758)

    def test_db_source_never_touches_the_wire(self):
        with patch.object(debate_store, "load_debate", return_value={"debateDesc": "x"}):
            with patch.object(debate_fetch, "fetch_debate", side_effect=AssertionError("hit the API")):
                assert debate_fetch.load_debate(18, 3, 1758, source="db") == {"debateDesc": "x"}

    def test_an_unknown_source_is_rejected_rather_than_guessed(self):
        with pytest.raises(ValueError, match="source must be"):
            debate_fetch.load_debate(18, 3, 1758, source="corpus")


class TestFallbackIsLoudWhereItMatters:
    """The bulk/single asymmetry: one stray HTTP call is fine, 64,921 are not."""

    def test_db_source_raises_on_a_debate_that_is_not_stored(self):
        with patch.object(debate_store, "load_debate", return_value=None):
            with pytest.raises(LookupError, match="not in the corpus"):
                debate_fetch.load_debate(18, 3, 9999, source="db")

    def test_db_source_lets_a_dead_postgres_through_rather_than_falling_back(self):
        # The failure this module exists to prevent: a connection error quietly
        # becoming per-debate HTTP across the whole corpus.
        with patch.object(debate_store, "load_debate", side_effect=OSError("connection refused")):
            with patch.object(debate_fetch, "fetch_debate", side_effect=AssertionError("fell back")):
                with pytest.raises(OSError):
                    debate_fetch.load_debate(18, 3, 1758, source="db")

    def test_auto_falls_back_to_the_wire_when_postgres_is_dead(self):
        # db_roster already promises the CLI works with no Postgres running.
        with patch.object(debate_store, "load_debate", side_effect=OSError("connection refused")):
            with patch.object(debate_fetch, "fetch_debate", return_value={"debateDesc": "wire"}):
                assert debate_fetch.load_debate(18, 3, 1758, source="auto")["debateDesc"] == "wire"

    def test_auto_falls_back_to_the_wire_for_a_debate_not_yet_imported(self):
        with patch.object(debate_store, "load_debate", return_value=None):
            with patch.object(debate_fetch, "fetch_debate", return_value={"debateDesc": "wire"}):
                assert debate_fetch.load_debate(18, 3, 9999, source="auto")["debateDesc"] == "wire"

    def test_auto_prefers_the_corpus_when_it_has_the_debate(self):
        with patch.object(debate_store, "load_debate", return_value={"debateDesc": "corpus"}):
            with patch.object(debate_fetch, "fetch_debate", side_effect=AssertionError("hit the API")):
                assert debate_fetch.load_debate(18, 3, 1758, source="auto")["debateDesc"] == "corpus"

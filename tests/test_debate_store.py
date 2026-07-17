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
        # The API sends a string date. The table holds a DATE. Both paths must give the same type.
        assert _row_to_payload(ROW)["debateDate"] == "14/12/2024"

    def test_mpcode_stays_an_int(self):
        # resolve_speaker compares mpCodes by identity, so the type must stay int.
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
        # The rebuilt payload goes to the parser with no API call.
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
    def test_db_source_raises_on_a_debate_that_is_not_stored(self):
        with patch.object(debate_store, "load_debate", return_value=None):
            with pytest.raises(LookupError, match="not in the corpus"):
                debate_fetch.load_debate(18, 3, 9999, source="db")

    def test_db_source_lets_a_dead_postgres_through_rather_than_falling_back(self):
        # A connection error must not become per-debate HTTP calls.
        with patch.object(debate_store, "load_debate", side_effect=OSError("connection refused")):
            with patch.object(debate_fetch, "fetch_debate", side_effect=AssertionError("fell back")):
                with pytest.raises(OSError):
                    debate_fetch.load_debate(18, 3, 1758, source="db")

    def test_auto_falls_back_to_the_wire_when_postgres_is_dead(self):
        # db_roster must work with no Postgres running.
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

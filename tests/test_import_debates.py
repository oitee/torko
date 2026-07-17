"""
The debate importer's shred: two API responses -> one `debates` row.

These tests are offline and pin the *pure* half of scripts/import_debates.py --
the field mapping, the date parsing, and the losslessness property. The network
and database halves are not tested here; they are exercised by running the
script (see internal_docs/022_DEBATE_IMPORT.md).

The mapping is where the damage would be. It is not obvious, and one part of it
is actively misleading: `debateType` names an int in the search record and a
string in the details payload. Reading the wrong one yields 65,000 rows of
plausible-looking nonsense, with nothing failing.

Fixtures below are trimmed from real responses (LS18 s7 db5714, LS13 s14 db7766).
"""
import json
from datetime import date

import pytest
import requests

from scripts import import_debates
from scripts.import_debates import (
    parse_sansad_date,
    rebuild_payload,
    row_from_responses,
    search_page_retrying,
    unmodelled_keys,
)

# A real search record. Note `debateType` is an INT here and `debateDesc` and
# `contents` are empty -- both are always empty in the search response (90/90).
SEARCH = {
    "loksabha": 18,
    "session": 7,
    "dbSlno": 5714,
    "debateTitle": "Need for clarification on carrying capacity assessment",
    "contents": "",
    "memberName": ["Shri Rajiv Pratap Rudy"],
    "debateType": 39,
    "debateTypeDesc": "PRIVATE MEMBERS' BILLS",
    "debateDate": "11/03/2026",
    "debateDesc": "",
    "keywordUsed": ["Ecological Balance"],
    "mpPartDetailList": [{"mpName": "Shri Rajiv Pratap Rudy", "mpCode": 4844, "mpPartCode": 1}],
}

# The matching details payload. `debateType` is a STRING here -- the same key
# name, a different field. `debateDesc` and `contents` carry the real values.
PAYLOAD = {
    "contents": "11-03-2026 Need for clarification on carrying capacity",
    "debateDesc": '<A name="4844*1"></A><b>SHRI RAJIV PRATAP RUDY:</b> Thank you.',
    "debateDate": "11/03/2026",
    "debateType": "PRIVATE MEMBERS' BILLS",
    "mpPartDetailList": [{"mpName": "Shri Rajiv Pratap Rudy", "mpCode": 4844, "mpPartCode": 1}],
}


class TestDebateTypeTrap:
    """`debateType` means different things in the two responses. Pin both."""

    def test_type_code_is_the_int_from_the_search_record(self):
        row = row_from_responses(18, SEARCH, PAYLOAD)
        assert row["debate_type_code"] == 39

    def test_type_description_is_the_string(self):
        row = row_from_responses(18, SEARCH, PAYLOAD)
        assert row["debate_type"] == "PRIVATE MEMBERS' BILLS"

    def test_the_payloads_debateType_is_the_description_not_the_code(self):
        # The confusion this guards: payload.debateType == search.debateTypeDesc
        # (verified live, 36/36). Taking debate_type_code from the payload would
        # silently store a string.
        assert PAYLOAD["debateType"] == SEARCH["debateTypeDesc"]
        row = row_from_responses(18, SEARCH, PAYLOAD)
        assert row["debate_type_code"] != PAYLOAD["debateType"]


class TestFieldsComeFromTheRightResponse:
    """Neither response is complete; each field has exactly one real source."""

    def test_text_comes_from_the_payload_not_the_empty_search_copy(self):
        row = row_from_responses(18, SEARCH, PAYLOAD)
        assert row["raw_html"] == PAYLOAD["debateDesc"]
        assert row["raw_html"] != SEARCH["debateDesc"]

    def test_contents_comes_from_the_payload(self):
        row = row_from_responses(18, SEARCH, PAYLOAD)
        assert row["contents"] == PAYLOAD["contents"]

    def test_title_comes_from_the_search_record(self):
        # The payload has no title at all.
        assert "debateTitle" not in PAYLOAD
        row = row_from_responses(18, SEARCH, PAYLOAD)
        assert row["title"] == SEARCH["debateTitle"]

    def test_keywords_and_member_names_come_from_the_search_record(self):
        row = row_from_responses(18, SEARCH, PAYLOAD)
        assert row["keywords"] == ["Ecological Balance"]
        assert row["member_names"] == ["Shri Rajiv Pratap Rudy"]

    def test_natural_key_and_source_url(self):
        row = row_from_responses(18, SEARCH, PAYLOAD)
        assert (row["loksabha"], row["session"], row["dbslno"]) == (18, 7, 5714)
        assert "ls=18&session=7&dbslno=5714" in row["source_url"]

    def test_sha256_is_of_the_raw_html(self):
        import hashlib
        row = row_from_responses(18, SEARCH, PAYLOAD)
        assert row["raw_html_sha256"] == hashlib.sha256(PAYLOAD["debateDesc"].encode()).hexdigest()


class TestParseSansadDate:
    """Total by design: one bad date must not end a three-hour run."""

    def test_reads_day_first(self):
        # 05/02/2004 is 5 February, not 2 May.
        assert parse_sansad_date("05/02/2004") == date(2004, 2, 5)

    def test_missing_and_empty_are_none_not_an_exception(self):
        assert parse_sansad_date(None) is None
        assert parse_sansad_date("") is None

    def test_malformed_is_none_not_an_exception(self):
        assert parse_sansad_date("2004-02-05") is None
        assert parse_sansad_date("garbage") is None
        assert parse_sansad_date("32/13/2004") is None


class TestEmptyAndMissingFields:
    """An empty debate is legitimate; a crash is not."""

    def test_empty_debate_desc_gives_empty_raw_html_not_none(self):
        # raw_html is NOT NULL: '' means "fetched, genuinely empty", while a
        # missing ROW means "not fetched yet". Resume depends on that.
        row = row_from_responses(18, SEARCH, {**PAYLOAD, "debateDesc": ""})
        assert row["raw_html"] == ""

    def test_null_mp_list_becomes_an_empty_json_array(self):
        row = row_from_responses(18, SEARCH, {**PAYLOAD, "mpPartDetailList": None})
        assert json.loads(row["mp_list_raw"]) == []

    def test_null_keywords_and_members_become_empty_lists(self):
        row = row_from_responses(18, {**SEARCH, "keywordUsed": None, "memberName": None}, PAYLOAD)
        assert row["keywords"] == []
        assert row["member_names"] == []


class TestUnmodelledKeys:
    """`extra` is the difference between discovering a new field and losing it."""

    def test_known_keys_produce_no_extra(self):
        assert unmodelled_keys(PAYLOAD, SEARCH) == {}
        assert json.loads(row_from_responses(18, SEARCH, PAYLOAD)["extra"]) == {}

    def test_an_unexpected_key_is_captured_and_namespaced(self):
        extra = unmodelled_keys({**PAYLOAD, "newThing": 42}, {**SEARCH, "alsoNew": "x"})
        assert extra == {"payload.newThing": 42, "search.alsoNew": "x"}

    def test_an_unexpected_key_survives_into_the_row(self):
        row = row_from_responses(18, SEARCH, {**PAYLOAD, "surprise": ["a"]})
        assert json.loads(row["extra"]) == {"payload.surprise": ["a"]}


class TestShredIsLossless:
    """The justification for typed columns over a raw JSON blob.

    If this breaks, the schema has begun losing something the API sent, and
    every stored debate would need refetching to recover it.
    """

    def test_payload_rebuilds_exactly_from_the_row(self):
        row = row_from_responses(18, SEARCH, PAYLOAD)
        assert rebuild_payload(row) == PAYLOAD

    def test_rebuild_survives_an_empty_debate(self):
        payload = {**PAYLOAD, "debateDesc": "", "mpPartDetailList": []}
        assert rebuild_payload(row_from_responses(18, SEARCH, payload)) == payload

    def test_rebuild_handles_a_legacy_era_payload(self):
        # Old-era text: disguised Hindi, no recent-style ID tag. The importer
        # must not care -- it stores bytes and asks no questions about era.
        payload = {
            "contents": " 03-02-2004 Discussion",
            "debateDesc": "<b>gÉÉÒ VÉMÉnÉÎà¤ÉBÉEÉ {ÉÉãÉ:</b> ¨ÉèÆ",
            "debateDate": "03/02/2004",
            "debateType": "BUDGET (RAILWAYS)",
            "mpPartDetailList": [{"mpName": "Pal, Shri Jagdambika", "mpCode": 584, "mpPartCode": 1}],
        }
        search = {**SEARCH, "loksabha": 13, "session": 14, "dbSlno": 7766,
                  "debateTypeDesc": "BUDGET (RAILWAYS)", "debateDate": "03/02/2004"}
        row = row_from_responses(13, search, payload)
        assert rebuild_payload(row) == payload
        assert row["debate_date"] == date(2004, 2, 3)


class TestSearchPageRetrying:
    """The search walk's tolerance for an erratic endpoint.

    This is the failure that actually killed runs. The search endpoint is not
    blocking us and is not down -- it is *uneven*, measured at a 0.2s median
    with a tail past 27s on the same term minutes apart. A single ConnectTimeout
    inside the walk used to propagate all the way out of main() and end a run
    that had already imported 7,616 debates.

    The contract pinned here: transient failures are retried and the walk
    continues; total failure still raises, because enumeration cannot proceed on
    a partial walk and a term silently imported minus one page would be a data
    gap nobody would ever notice.
    """

    def test_a_transient_timeout_does_not_end_the_walk(self, monkeypatch):
        calls = []

        def flaky(loksabha, page, size=100):
            calls.append(page)
            if len(calls) == 1:
                raise requests.ConnectTimeout("connect timed out")
            return {"records": [{"session": 1, "dbSlno": 7}]}

        monkeypatch.setattr(import_debates, "search_page", flaky)
        monkeypatch.setattr(import_debates.time, "sleep", lambda _: None)

        assert search_page_retrying(15, 3)["records"] == [{"session": 1, "dbSlno": 7}]
        assert len(calls) == 2

    def test_it_gives_up_loudly_rather_than_walking_a_partial_term(self, monkeypatch):
        def always_down(loksabha, page, size=100):
            raise requests.ConnectTimeout("connect timed out")

        monkeypatch.setattr(import_debates, "search_page", always_down)
        monkeypatch.setattr(import_debates.time, "sleep", lambda _: None)

        with pytest.raises(requests.ConnectTimeout):
            search_page_retrying(15, 3, retries=2)

    def test_it_retries_up_to_the_limit_before_succeeding(self, monkeypatch):
        attempts = []

        def slow_to_recover(loksabha, page, size=100):
            attempts.append(page)
            if len(attempts) < 4:
                raise requests.ReadTimeout("read timed out")
            return {"records": []}

        monkeypatch.setattr(import_debates, "search_page", slow_to_recover)
        monkeypatch.setattr(import_debates.time, "sleep", lambda _: None)

        assert search_page_retrying(15, 3, retries=4) == {"records": []}
        assert len(attempts) == 4


class TestEnumerateRefsProgress:
    """The walk must report, because silence is what got misread as a hang.

    LS15 is 113 search pages before a single debate is fetched -- minutes of
    work. With no output and stdout block-buffered into a redirected file, a
    healthy run and a hung one produce byte-identical evidence: nothing.
    """

    def test_the_walk_reports_progress_and_dedups(self, monkeypatch, capsys):
        def two_pages(loksabha, page, size=100):
            if page == 1:
                return {"_metadata": {"totalPages": 2},
                        "records": [{"session": 1, "dbSlno": 1}, {"session": 1, "dbSlno": 2}]}
            # dbSlno 2 repeats -- the search API really does serve a debate twice.
            return {"records": [{"session": 1, "dbSlno": 2}, {"session": 1, "dbSlno": 3}]}

        monkeypatch.setattr(import_debates, "search_page", two_pages)
        refs = import_debates.enumerate_refs(15)

        assert sorted(r["dbSlno"] for r in refs) == [1, 2, 3]
        out = capsys.readouterr().out
        assert "walking 2 search pages" in out
        assert "search walk done, 3 distinct debates" in out

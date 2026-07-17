import json
from datetime import date

from scripts.import_debates import (
    parse_sansad_date,
    rebuild_payload,
    row_from_responses,
    unmodelled_keys,
)

# A real search record. debateType is an INT here. debateDesc and contents are always empty.
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

# The matching details payload. debateType is a STRING here. debateDesc and contents hold the values.
PAYLOAD = {
    "contents": "11-03-2026 Need for clarification on carrying capacity",
    "debateDesc": '<A name="4844*1"></A><b>SHRI RAJIV PRATAP RUDY:</b> Thank you.',
    "debateDate": "11/03/2026",
    "debateType": "PRIVATE MEMBERS' BILLS",
    "mpPartDetailList": [{"mpName": "Shri Rajiv Pratap Rudy", "mpCode": 4844, "mpPartCode": 1}],
}


class TestDebateTypeTrap:
    def test_type_code_is_the_int_from_the_search_record(self):
        row = row_from_responses(18, SEARCH, PAYLOAD)
        assert row["debate_type_code"] == 39

    def test_type_description_is_the_string(self):
        row = row_from_responses(18, SEARCH, PAYLOAD)
        assert row["debate_type"] == "PRIVATE MEMBERS' BILLS"

    def test_the_payloads_debateType_is_the_description_not_the_code(self):
        # debate_type_code comes from the search record, not from the payload string.
        assert PAYLOAD["debateType"] == SEARCH["debateTypeDesc"]
        row = row_from_responses(18, SEARCH, PAYLOAD)
        assert row["debate_type_code"] != PAYLOAD["debateType"]


class TestFieldsComeFromTheRightResponse:
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
    def test_payload_rebuilds_exactly_from_the_row(self):
        row = row_from_responses(18, SEARCH, PAYLOAD)
        assert rebuild_payload(row) == PAYLOAD

    def test_rebuild_survives_an_empty_debate(self):
        payload = {**PAYLOAD, "debateDesc": "", "mpPartDetailList": []}
        assert rebuild_payload(row_from_responses(18, SEARCH, payload)) == payload

    def test_rebuild_handles_a_legacy_era_payload(self):
        # Old-era text: disguised Hindi, no recent-style ID tag. The importer stores bytes for any era.
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

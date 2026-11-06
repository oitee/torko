"""The plain-language question reader of /api/ask: rules, guards on the LLM answer, and the merge. No network, no database."""
from pages.ask import build_vocab, checked_llm, merge, needs_llm, read_as, read_rules, year_filters

MEMBERS = [(1994, "Shashi Tharoor"), (1156, "Asaduddin Owaisi"), (1157, "Sultan Salahuddin Owaisi"),
           (615, "Smriti Zubin Irani"), (2216, "Lalu Prasad"), (77, "Ram Bihari")]
PARTIES = [("BJP", "Bharatiya Janata Party"), ("INC", "Indian National Congress"), ("SP", "Samajwadi Party"),
           ("CPI(M)", "Communist Party of India (Marxist)"), ("AITC", "All India Trinamool Congress")]
STATES = ["Kerala", "Bihar", "Tamil Nadu"]
TAGS = [("Fishermen", "topic", []), ("Floods", "topic", []), ("Kerala", "place", []), ("Bihar", "place", []),
        ("Bihari", "topic", []), ("Goods and Services Tax (GST)", "law", ["Goods and Service Tax"]),
        ("Farmers' Suicide", "topic", ["Farmer Suicide"]), ("Speeches", "topic", []), ("Price Rise", "topic", ["Inflation"]),
        ("Prime Minister", "role", []), ("Manipur Violence", "topic", []), ("Manipur", "place", []),
        ("Lok Sabha", "institution", []), ("Statement", "topic", []), ("Ministers", "topic", []), ("Education", "topic", [])]
VOCAB = build_vocab(MEMBERS, PARTIES, STATES, TAGS)


def rules(q):
    return read_rules(q, VOCAB)["params"]


def test_reads_state_tag_and_year_of_the_example_question():
    assert rules("What did Kerala MPs say about fishermen after 2019?") == {
        "state": "Kerala", "tag": "fishermen", "date_from": "2020-01-01"}


def test_a_state_without_mps_is_a_place():
    assert rules("Shashi Tharoor on Kerala floods") == {"member": "1994", "place": "kerala", "tag": "floods"}
    assert rules("Kerala ke MPs ne fishermen par kya kaha")["state"] == "Kerala"
    assert rules("MPs from Bihar on floods")["state"] == "Bihar"


def test_a_name_of_two_members_is_dropped_not_guessed():
    got = read_rules("Owaisi on price rise", VOCAB)
    assert got["params"] == {"tag": "price-rise"}
    assert got["dropped"] == [{"text": "Owaisi", "why": "2 members have this name"}]


def test_first_and_last_word_of_a_long_name_find_the_member():
    assert rules("Smriti Irani on floods")["member"] == "615"


def test_a_surname_never_wins_over_a_tag_of_the_same_word():
    assert rules("speeches on Bihari migrants") == {"tag": "bihari"}


def test_acronym_in_brackets_and_apostrophe_and_plural():
    assert rules("BJP on GST in the 17th Lok Sabha") == {"party": "BJP", "tag": "goods-and-services-tax-gst", "term": "17"}
    assert rules("who raised farmers suicide")["tag"] == "farmers-suicide"
    assert rules("who raised farmer's suicides")["tag"] == "farmers-suicide"


def test_question_words_are_not_tags_and_not_search_words():
    got = read_rules("speeches about floods", VOCAB)
    assert got["params"] == {"tag": "floods"}
    assert got["words"] == ""


def test_the_longest_name_wins():
    assert rules("Manipur violence in 2023") == {"tag": "manipur-violence", "date_from": "2023-01-01", "date_to": "2023-12-31"}


def test_party_aliases_and_codes_that_are_common_words():
    assert rules("Congress MPs on floods")["party"] == "INC"
    assert rules("CPI(M) members on floods")["party"] == "CPI(M)"
    assert rules("SP on floods")["party"] == "SP"
    assert "party" not in rules("sp on floods")


def test_role_tags_are_not_filters():
    assert "tag" not in rules("what did the prime minister say")


def test_who_asks_for_members_with_most_speeches():
    assert rules("Which MPs spoke most about floods?") == {"tag": "floods", "view": "members", "sort": "most"}
    assert rules("naxal par sabse zyada kisne bola")["view"] == "members"


def test_year_forms():
    assert year_filters("between 2004 and 2009")[0] == {"date_from": "2004-01-01", "date_to": "2009-12-31"}
    assert year_filters("before 2014")[0] == {"date_to": "2013-12-31"}
    assert year_filters("since 2014")[0] == {"date_from": "2014-01-01"}
    assert year_filters("2019 के बाद")[0] == {"date_from": "2020-01-01"}
    assert year_filters("2014 se pehle")[0] == {"date_to": "2013-12-31"}
    assert year_filters("in 2019")[0] == {"date_from": "2019-01-01", "date_to": "2019-12-31"}


def test_llm_is_needed_only_for_hindi_script_or_hindi_words():
    assert needs_llm("बिहार में बाढ़", [])
    assert needs_llm("Kerala ke MPs", [])
    assert not needs_llm("Kerala MPs on fishermen", [])


def test_llm_names_are_checked_and_unknown_subjects_become_words():
    answer = {"members": ["Shashi Tharoor", "Nobody Known"], "parties": ["BJP", "XYZ"], "subjects": ["Floods", "Coal scam"],
              "places": ["Kerala"], "words": ["what did they say", "relief"]}
    got = checked_llm(answer, VOCAB, "question")
    assert got["params"] == {"member": "1994", "party": "BJP", "tag": "floods", "place": "kerala"}
    assert got["words"] == "Coal scam relief"


def test_llm_term_and_kind_need_their_own_words_in_the_question():
    assert "term" not in checked_llm({"term": 15}, VOCAB, "black money before 2014")["params"]
    assert checked_llm({"term": 17}, VOCAB, "17वीं लोकसभा में जीएसटी")["params"]["term"] == "17"
    assert "kind" not in checked_llm({"kind": "discussion"}, VOCAB, "जीएसटी पर बहस")["params"]
    assert checked_llm({"kind": "zero_hour"}, VOCAB, "zero hour on floods")["params"]["kind"] == "zero_hour"


def test_llm_dates_are_checked():
    got = checked_llm({"date_from": "2020-01-01", "date_to": "2019-12-31"}, VOCAB, "q")["params"]
    assert got == {"date_from": "2020-01-01"}
    assert checked_llm({"date_from": "soon"}, VOCAB, "q")["params"] == {}


def test_merge_keeps_the_rules_and_never_adds_a_state_for_a_place_of_the_same_name():
    r = read_rules("Tharoor ne Kerala floods par kya bola", VOCAB)
    llm = checked_llm({"member_states": ["Kerala"], "subjects": ["Floods"], "members": ["Shashi Tharoor"]}, VOCAB, "q")
    got = merge(r, llm)
    assert got["params"] == {"member": "1994", "place": "kerala", "tag": "floods"}


def test_read_as_line_order():
    picked = [{"key": "tag", "value": "floods", "label": "Floods", "text": "floods"},
              {"key": "member", "value": "1994", "label": "Shashi Tharoor", "text": "Tharoor"}]
    out = read_as(picked, {"tag": "floods", "member": "1994", "date_from": "2020-01-01", "view": "members"})
    assert [o["text"] for o in out] == ["by Shashi Tharoor", "on Floods", "from 1 Jan 2020", "members with the most speeches first"]


def test_daily_limit_stops_the_llm_call_and_the_rules_answer_stands(monkeypatch):
    import pages.ask as ask_mod
    calls = []
    monkeypatch.setattr(ask_mod, "load_vocab", lambda conn: VOCAB)
    monkeypatch.setattr(ask_mod, "stored_answer", lambda store, key: None)
    monkeypatch.setattr(ask_mod, "take_call", lambda store, limit: False)
    out = ask_mod.ask(None, "Kerala ke MPs ne fishermen par kya kaha", store=object(), llm=lambda *a: calls.append(a))
    assert calls == []
    assert out["llm"] == "daily limit"
    assert out["params"] == {"state": "Kerala", "tag": "fishermen"}


def test_a_failed_llm_call_keeps_the_rules_answer(monkeypatch):
    import pages.ask as ask_mod

    def boom(*a):
        raise RuntimeError("timeout")
    monkeypatch.setattr(ask_mod, "load_vocab", lambda conn: VOCAB)
    monkeypatch.setattr(ask_mod, "stored_answer", lambda store, key: None)
    monkeypatch.setattr(ask_mod, "take_call", lambda store, limit: True)

    class Conn:
        def execute(self, *a, **k):
            return []
    out = ask_mod.ask(Conn(), "बिहार में बाढ़", store=object(), llm=boom)
    assert out["llm"] == "failed"
    assert out["params"] == {"q": "बिहार बाढ़"}


def test_names_made_of_question_words_and_filler_words_do_not_narrow_the_list():
    got = read_rules("who is the speaker of lok sabha", VOCAB)
    assert "tag" not in got["params"] and got["words"] == "speaker"
    got = read_rules("best speeches on education", VOCAB)
    assert got["params"] == {"tag": "education"} and got["words"] == ""


def test_statement_by_minister_is_a_kind_not_two_tags():
    assert rules("statement by minister on floods") == {"kind": "statement", "tag": "floods"}

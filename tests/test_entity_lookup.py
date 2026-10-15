from entity_lookup import Entity, EntityDictionary, normalise, parse_counted
from scripts.extract_entities import mention_key


def make(*entities):
    return EntityDictionary.from_rows([{"name": n, "type": t, "speeches": s, "mentions": m} for n, t, s, m in entities])


FARMERS = ("Farmers", "group", 100, "farmers (5) | किसानों (4)")
NREGA = ("MGNREGA", "scheme", 50, "mgnrega (3)")


def names(result):
    return [r[0] for r in result]


def test_the_normalisation_is_the_same_as_the_mention_key_of_the_extraction():
    for value in ["Farmers  Union", "किसान‍ों", "A\tB\nC", "STRASSE straße", "﻿x​y"]:
        assert normalise(value) == mention_key(value)


def test_a_counted_cell_is_parsed_into_pairs():
    assert parse_counted("a (3) | b c (12) | broken") == [("a", 3), ("b c", 12)]


def test_a_mention_is_found_without_case():
    assert names(make(FARMERS).lookup("The FARMERS need help.")) == ["Farmers"]


def test_the_result_has_the_name_the_type_and_the_text_that_matched():
    assert make(FARMERS).lookup("Help the farmers now") == [("Farmers", "group", "farmers")]


def test_a_mention_inside_a_longer_english_word_does_not_match():
    d = make(("Farm", "group", 10, "farm (3)"))
    assert d.lookup("The farmland is dry and unfarmed.") == []
    assert names(d.lookup("The farm is dry.")) == ["Farm"]


def test_a_match_next_to_punctuation_is_accepted():
    d = make(FARMERS)
    for text in ["(farmers)", "farmers, who", "said \"farmers\"", "farmers.", "farmers’ income", "anti-farmers"]:
        assert names(d.lookup(text)) == ["Farmers"], text


def test_a_match_at_the_start_and_at_the_end_of_the_text_is_accepted():
    d = make(FARMERS)
    assert names(d.lookup("farmers")) == ["Farmers"]


def test_a_match_with_a_line_break_around_it_is_accepted():
    assert names(make(FARMERS).lookup("many\nfarmers\nwait")) == ["Farmers"]


def test_a_hindi_mention_matches_as_a_whole_word():
    assert names(make(FARMERS).lookup("देश के किसानों की आय बढ़ानी है")) == ["Farmers"]


def test_a_hindi_mention_does_not_match_before_a_vowel_sign_or_a_letter_of_the_same_word():
    d = make(("Farmers", "group", 10, "किसान (3)"))
    assert d.lookup("किसानों की बात") == []
    assert d.lookup("किसानी की बात") == []
    assert names(d.lookup("किसान की बात")) == ["Farmers"]


def test_a_hindi_mention_does_not_match_after_a_letter_of_a_longer_word():
    d = make(("Farmers", "group", 10, "किसान (3)"))
    assert d.lookup("अकिसान की बात") == []


def test_a_hindi_mention_before_the_danda_matches():
    assert names(make(("Farmers", "group", 10, "किसान (3)")).lookup("यह किसान।")) == ["Farmers"]


def test_a_zero_width_character_inside_the_text_does_not_break_a_match():
    assert names(make(FARMERS).lookup("far​mers are here")) == ["Farmers"]


def test_a_mention_with_extra_spaces_in_the_text_still_matches():
    d = make(("Rail", "institution", 10, "indian railways (3)"))
    assert names(d.lookup("the Indian   Railways run")) == ["Rail"]


def test_a_digit_next_to_the_match_is_not_a_boundary():
    d = make(("Article", "law", 10, "article 21 (3)"))
    assert d.lookup("see article 210 now") == []
    assert names(d.lookup("see article 21.")) == ["Article"]


def test_a_name_that_the_speech_already_has_is_skipped_without_case():
    assert make(FARMERS, NREGA).lookup("farmers and MGNREGA", {"FARMERS"}) == [("MGNREGA", "scheme", "mgnrega")]


def test_the_cap_keeps_the_most_specific_names():
    d = make(("Low", "law", 5, "lowword (3)"), ("High", "law", 90, "highword (3)"), ("Mid", "law", 40, "midword (3)"))
    assert names(d.lookup("lowword midword highword", k=2)) == ["Low", "Mid"]


def test_a_rare_name_ranks_before_a_common_name_with_the_same_number_of_matches():
    d = make(("Common", "place", 5000, "commonplace (3)"), ("Rare", "place", 4, "rareplace (3)"))
    assert names(d.lookup("commonplace rareplace")) == ["Rare", "Common"]


def test_a_common_name_with_many_matches_can_rank_before_a_rare_name_with_one_match():
    d = make(("Common", "place", 1000, "commonplace (3)"), ("Rare", "place", 100, "rareplace (3)"))
    text = "rareplace " + "commonplace " * 5
    assert names(d.lookup(text)) == ["Common", "Rare"]
    assert names(d.lookup("rareplace commonplace")) == ["Rare", "Common"]


def test_the_score_is_the_matches_times_the_log_of_source_speeches_over_name_speeches():
    import math
    d = EntityDictionary.from_rows([{"name": "A", "type": "law", "speeches": 10, "mentions": "aword (3)"}], source_speeches=1000)
    assert d.score(d.entities[0], 3) == 3 * math.log(100)


def test_names_with_the_same_score_are_in_name_order():
    d = make(("Beta", "law", 10, "betaword (3)"), ("Alpha", "law", 10, "alphaword (3)"))
    assert names(d.lookup("betaword alphaword")) == ["Alpha", "Beta"]


def test_the_matches_of_all_mentions_of_one_name_add_up():
    d = make(("One", "law", 100, "kisan (2) | farmers (9)"), ("Two", "law", 100, "other (3)"))
    assert names(d.lookup("other kisan farmers")) == ["One", "Two"]
    assert d.find("kisan farmers kisan")["one"][2] == 3


def test_a_spelling_variant_of_a_name_that_the_speech_has_is_skipped():
    d = make(("Siddharthnagar", "place", 10, "siddharthnagar (3)"))
    assert d.lookup("siddharthnagar", {"Siddharth Nagar"}) == []


def test_spelling_variants_have_the_same_key():
    from entity_lookup import spelling_key
    assert spelling_key("Insolvency and Bankruptcy Code 2016") == spelling_key("Insolvency and Bankruptcy Code, 2016")
    assert spelling_key("Siddharthnagar") == spelling_key("Siddharth Nagar")
    assert spelling_key("Rae Bareli") == spelling_key("Raebareli")
    assert spelling_key("Employees' Provident Fund") == spelling_key("Employees Provident Fund")


def test_names_that_differ_in_a_digit_have_different_keys():
    from entity_lookup import spelling_key
    assert spelling_key("Article 21") != spelling_key("Article 12")
    assert spelling_key("Article 21") != spelling_key("Article 2 1")
    assert spelling_key("Article 48") != spelling_key("Article 48A")
    assert spelling_key("Act 1956") != spelling_key("Act 1965")


def test_hindi_names_keep_their_letters_in_the_key():
    from entity_lookup import spelling_key
    assert spelling_key("किसान") != spelling_key("जवान")
    assert spelling_key("लोक सभा") == spelling_key("लोकसभा")


def test_the_words_of_a_mention_end_at_punctuation_and_spaces():
    from entity_lookup import office_word_tokens
    assert office_word_tokens("PM, Modi-ji") == ["pm", "modi", "ji"]
    assert office_word_tokens("प्रधानमंत्री जी") == ["प्रधानमंत्री", "जी"]


def test_the_default_cap_is_8():
    d = make(*[(f"N{i}", "law", 100 - i, f"word{chr(97 + i)}xx (3)") for i in range(12)])
    text = " ".join(f"word{chr(97 + i)}xx" for i in range(12))
    assert len(d.lookup(text)) == 8


def test_a_mention_that_the_dictionary_does_not_hold_never_matches():
    d = make(("Alpha", "law", 10, "alpha word (3)"))
    assert d.lookup("a shared word appears here") == []


def test_an_entity_is_returned_once_when_several_of_its_mentions_match_and_the_most_used_one_is_shown():
    d = make(("Farmers", "group", 10, "kisan (2) | farmers (9)"))
    assert d.lookup("kisan and farmers") == [("Farmers", "group", "farmers")]


def test_an_empty_text_gives_no_result():
    assert make(FARMERS).lookup("") == []


def test_the_dictionary_loads_from_a_csv_file(tmp_path):
    path = tmp_path / "d.csv"
    path.write_text("name,type,speeches,mentions\nFarmers,group,10,farmers (3) | किसान (2)\n", encoding="utf-8-sig")
    assert names(EntityDictionary.load(path).lookup("किसान")) == ["Farmers"]


def shimla_dictionary():
    return EntityDictionary([Entity("Shimla", "place", 300, (("शिमला", 50),)),
                             Entity("Shimla Agreement", "law", 40, (("शिमला एग्रीमेंट", 30),))], source_speeches=50_000)


def test_a_name_inside_a_longer_dictionary_name_is_not_added():
    assert names(shimla_dictionary().lookup("शिमला एग्रीमेंट को देखिए")) == ["Shimla Agreement"]


def test_a_name_inside_a_longer_name_that_the_speech_has_already_is_not_added():
    # The extraction holds the agreement, so the agreement is skipped. Its words still hide Shimla.
    assert shimla_dictionary().lookup("शिमला एग्रीमेंट को देखिए", {"Shimla Agreement"}) == []


def test_a_name_said_once_on_its_own_is_added_even_when_another_match_is_inside_a_longer_name():
    assert names(shimla_dictionary().lookup("शिमला एग्रीमेंट शिमला में हुआ")) == ["Shimla", "Shimla Agreement"]


def test_a_name_inside_the_words_of_an_extracted_name_is_not_added():
    d = EntityDictionary([Entity("Kheri", "place", 30, (("खीरी", 20),))], source_speeches=50_000)
    text = "मेरे क्षेत्र लखीमपुर खीरी में"
    assert names(d.lookup(text)) == ["Kheri"]
    assert d.lookup(text, longer_mentions=["लखीमपुर खीरी"]) == []


def test_an_equal_match_is_not_a_longer_match():
    d = EntityDictionary([Entity("Kheri", "place", 30, (("खीरी", 20),))], source_speeches=50_000)
    assert names(d.lookup("खीरी जिला", longer_mentions=["खीरी"])) == ["Kheri"]


def test_a_skipped_name_frees_its_place_under_the_cap():
    d = shimla_dictionary()
    d2 = EntityDictionary(d.entities + [Entity("Mandi", "place", 30_000, (("मंडी", 10),))], source_speeches=50_000)
    assert names(d2.lookup("शिमला एग्रीमेंट और मंडी", {"Shimla Agreement"}, k=1)) == ["Mandi"]

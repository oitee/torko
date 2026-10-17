from entity_lookup import Entity, EntityDictionary
from scripts.add_candidates import (GENERAL_TAGS_FILE, dictionary_rows, load_general_tags, named_mentions, next_position,
                                   summary_tag_rows, without_general)

LLM = [{"list": "topic", "position": 1, "name": "Railways", "type": "topic", "mention": "railway", "mention_found": True},
       {"list": "topic", "position": 2, "name": "Safety", "type": "topic", "mention": "safety", "mention_found": True},
       {"list": "other", "position": 1, "name": "Odisha", "type": "place", "mention": "Odisha", "mention_found": True}]


def dictionary():
    return EntityDictionary([Entity("Odisha", "place", 900, (("Odisha", 500),)),
                             Entity("East Coast Railway", "institution", 40, (("East Coast Railway", 30),)),
                             Entity("Khurda Road", "place", 12, (("Khurda Road", 10),))], source_speeches=50_000)


def test_next_position_follows_the_last_item_of_the_same_list():
    assert next_position(LLM, "topic") == 3
    assert next_position(LLM, "other") == 2
    assert next_position([], "other") == 1


def test_dictionary_rows_skip_a_name_the_speech_has_and_continue_the_positions():
    text = "The East Coast Railway in Odisha must stop at Khurda Road. Khurda Road needs a bridge."
    rows = dictionary_rows(LLM, text, dictionary(), k=8)
    assert [r["name"] for r in rows] == ["Khurda Road", "East Coast Railway"]
    assert [r["position"] for r in rows] == [2, 3]
    assert rows[0]["evidence"] == {"matches": 2, "rank": 1}
    assert all(r["list"] == "other" and r["mention_found"] and r["tag_id"] is None for r in rows)


def test_dictionary_rows_obey_the_cap():
    text = "The East Coast Railway must stop at Khurda Road."
    assert len(dictionary_rows(LLM, text, dictionary(), k=1)) == 1


def test_summary_tag_rows_keep_the_tag_and_its_evidence():
    near = [{"tag_id": 11, "tag": "New Railway Line", "type": "topic", "distance": 0.36312, "rank": 1},
            {"tag_id": 12, "tag": "Bareilly", "type": "place", "distance": 0.396, "rank": 2}]
    rows = summary_tag_rows(LLM, near)
    assert [(r["position"], r["tag_id"], r["type"]) for r in rows] == [(3, 11, "topic"), (4, 12, "place")]
    assert rows[0]["evidence"] == {"distance": 0.3631, "rank": 1}
    assert all(r["list"] == "topic" and r["mention"] == "" and not r["mention_found"] for r in rows)


def test_a_place_inside_the_words_of_an_extracted_law_is_not_added():
    d = EntityDictionary([Entity("Andhra Pradesh", "place", 900, (("Andhra Pradesh", 500),))], source_speeches=50_000)
    act = {"list": "other", "position": 1, "name": "Andhra Pradesh Reorganisation Act", "type": "law",
           "mention": "Andhra Pradesh Reorganisation Act", "mention_found": True}
    text = "The Andhra Pradesh Reorganisation Act promised a university."
    assert dictionary_rows([act], text, d, k=8) == []
    assert [r["name"] for r in dictionary_rows([], text, d, k=8)] == ["Andhra Pradesh"]


def test_a_topic_or_group_phrase_never_hides_a_dictionary_match():
    items = [{"type": "topic", "mention": "the youth have no jobs", "mention_found": True},
             {"type": "group", "mention": "poor farmers", "mention_found": True},
             {"type": "place", "mention": "Jammu and Kashmir", "mention_found": True},
             {"type": "law", "mention": "an act the model guessed", "mention_found": False}]
    assert named_mentions(items) == ["Jammu and Kashmir"]


def test_a_general_tag_is_never_a_recognised_tag_and_the_next_tag_takes_its_place():
    near = [{"tag": "Members", "rank": 1}, {"tag": "New Railway Line", "rank": 2},
            {"tag": "Parliament", "rank": 3}, {"tag": "Railway Projects", "rank": 4}, {"tag": "Bareilly", "rank": 5}]
    kept = without_general(near, frozenset({"Members", "Parliament"}), 2)
    assert [(t["tag"], t["rank"]) for t in kept] == [("New Railway Line", 2), ("Railway Projects", 4)]


def test_the_general_tag_file_holds_the_house_words():
    general = load_general_tags(GENERAL_TAGS_FILE)
    assert {"Members", "Parliament", "Statement", "Government Of India"} <= general
    assert "Law Amendment" in general
    assert "Demands For Grants" not in general

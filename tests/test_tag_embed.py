import math

import pytest

from scripts.embed_tags import to_embed
from scripts.load_tags import parse_rows
from scripts.tag_bakeoff import best_rank
from tag_embed import build_input_text, clean_aliases, input_hash, normalise, to_pgvector


def test_input_text_holds_name_aliases_type_domain_and_description():
    text = build_input_text("Road Construction", "topic", "Roads and Highways",
                            "Building or improving roads and highways.", ["Road Development", "Road Projects"])
    assert text == ("Road Construction. Also called: Road Development, Road Projects. Type: topic. "
                    "Domain: Roads and Highways. Building or improving roads and highways.")


def test_input_text_leaves_out_missing_aliases_and_domain():
    assert build_input_text("Bombay", "place", None, "City in western India", []) == \
        "Bombay. Type: place. City in western India."


def test_aliases_lose_outer_spaces_doubles_and_the_tag_name():
    assert clean_aliases("Caste Census", [" Caste Census", "Jati Census ", "jati census"]) == ["Jati Census"]


def test_normalise_gives_length_one_and_refuses_zeros():
    v = normalise([3.0, 4.0])
    assert v == [0.6, 0.8] and math.isclose(sum(x * x for x in v), 1.0)
    with pytest.raises(ValueError):
        normalise([0.0, 0.0])


def test_pgvector_text_form():
    assert to_pgvector([0.5, -0.25]) == "[0.5,-0.25]"


def test_only_a_changed_or_new_tag_is_embedded_again():
    tags = [{"id": 1, "tag": "Tea", "type": "topic", "domain": None, "description": "Tea crop.", "aliases": []},
            {"id": 2, "tag": "Coffee", "type": "topic", "domain": None, "description": "Coffee crop.", "aliases": []},
            {"id": 3, "tag": "Jute", "type": "topic", "domain": None, "description": "Jute crop.", "aliases": []}]
    stored = {1: input_hash("Tea. Type: topic. Tea crop."), 2: "old hash"}
    assert [t["id"] for t in to_embed(tags, stored)] == [2, 3]


def test_best_rank_takes_the_first_acceptable_tag():
    ranked = ["Drought", "Bundelkhand", "Floods"]
    assert best_rank(ranked, ["Floods", "Bundelkhand"]) == 2
    assert best_rank(ranked, ["NONE", "Floods"]) == 3


def test_best_rank_is_none_for_a_none_only_pair_and_fails_on_an_unknown_tag():
    assert best_rank(["Drought"], ["NONE"]) is None
    with pytest.raises(ValueError):
        best_rank(["Drought"], ["Nowhere"])


def test_parse_rows_turns_dashes_into_null_and_empty_lists(tmp_path):
    f = tmp_path / "t.tsv"
    f.write_text("tag\ttype\tsubtype\tdomain\tdescription\taliases\tdebate_count\n"
                 "Bombay\tplace\tcity\t-\tCity.\t-\t8\n"
                 "Tea\ttopic\t\tAgriculture and Farmers\tTea crop.\tTea Crop|Tea Gardens\t5\n", encoding="utf-8")
    rows = parse_rows(f)
    assert rows[0]["domain"] is None and rows[0]["aliases"] == [] and rows[0]["subtype"] == "city"
    assert rows[1]["subtype"] is None and rows[1]["aliases"] == ["Tea Crop", "Tea Gardens"]
    assert rows[1]["debate_count"] == 5


def test_parse_rows_refuses_a_tag_name_with_outer_spaces(tmp_path):
    f = tmp_path / "t.tsv"
    f.write_text("tag\ttype\tsubtype\tdomain\tdescription\taliases\tdebate_count\n"
                 " Caste Census\tlaw\t\t-\tCensus by caste.\t-\t10\n", encoding="utf-8")
    with pytest.raises(SystemExit):
        parse_rows(f)

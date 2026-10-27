import csv

import pytest

from scripts.build_party_colours import legend_colours, pick_colours
from scripts.load_party_history import PARTY_COLOURS, read_party_colours

LEGEND = ('<span class="legend-color" style="border:1px solid black;background-color:#00bfff">&#160;</span>&#160;'
          '<a href="/wiki/Jammu_%26_Kashmir_National_Conference" title="x">JKNC</a>'
          '<span class="legend-color" style="background-color:#FF9933">&#160;</span>'
          '<a href="/wiki/BJP" title="BJP">BJP</a>')


def test_legend_colours_reads_the_article_and_follows_redirects():
    out = legend_colours(LEGEND, {"BJP": "Bharatiya Janata Party"})
    assert out == [("Jammu & Kashmir National Conference", "#00BFFF"), ("Bharatiya Janata Party", "#FF9933")]


def test_pick_colours_takes_the_latest_term_and_drops_rows_with_no_code():
    found = [(18, "Trinamool", "#13D6B6"), (14, "Trinamool", "#20C646"), (18, "Others", "#DDDDBB")]
    assert pick_colours(found, {"Trinamool": "AITC"}) == {"AITC": ("#13D6B6", "Trinamool", 18)}


def test_read_party_colours_refuses_a_bad_colour(tmp_path):
    p = tmp_path / "c.tsv"
    p.write_text("code\tcolour\twiki_article\tterm\nINC\t#00bfff\tx\t18\nBJP\torange\tx\t18\n", encoding="utf-8")
    with pytest.raises(SystemExit):
        read_party_colours(p)


def test_the_tracked_file_reads_and_has_one_row_per_code():
    colours = read_party_colours(PARTY_COLOURS)
    with open(PARTY_COLOURS, encoding="utf-8", newline="") as f:
        codes = [r["code"] for r in csv.DictReader(f, delimiter="\t")]
    assert len(codes) == len(set(codes)) == len(colours)
    assert colours["INC"] == "#00BFFF" and colours["BJP"] == "#FF9933"

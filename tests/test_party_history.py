import json
from pathlib import Path

import pytest
from bs4 import BeautifulSoup

import party_history as ph

RAW = Path(__file__).resolve().parent.parent / "data" / "party_history" / "raw"


def _page(table_rows: str, header: str = "<tr><th>No.</th><th>Constituency</th><th>Name of elected M.P.</th>"
          "<th colspan='2'>Party affiliation</th></tr>", state: str = "Bihar") -> str:
    return f"<h2>{state}</h2><table>{header}{table_rows}</table>"


def _party(title: str, shown: str | None = None) -> str:
    return f"<td></td><td><a href='/wiki/{title.replace(' ', '_')}' title='{title}'>{shown or title}</a></td>"


def _member(title: str, note: str = "") -> str:
    return f"<a href='/wiki/{title.replace(' ', '_')}' title='{title}'>{title}</a>{note}"


# --- the table grid ---------------------------------------------------------------------------

def test_grid_copies_a_rowspan_cell_into_each_row():
    html = "<table><tr><td rowspan='2'>A</td><td>B</td></tr><tr><td>C</td></tr></table>"
    grid = ph.table_grid(BeautifulSoup(html, "html.parser").table)
    assert [[c.get_text() for c in row] for row in grid] == [["A", "B"], ["A", "C"]]


def test_grid_copies_a_colspan_cell_into_each_column():
    html = "<table><tr><td colspan='2'>A</td><td>B</td></tr></table>"
    grid = ph.table_grid(BeautifulSoup(html, "html.parser").table)
    assert [c.get_text() for c in grid[0]] == ["A", "A", "B"]


# --- the page reader --------------------------------------------------------------------------

def test_a_party_cell_with_rowspan_gives_its_party_to_each_row():
    # 13th list, Andhra Pradesh: one Telugu Desam cell covers Hanamkonda and Warangal.
    rows = ph.parse_wiki_members(_page(
        f"<tr><th>38</th><td>Hanamkonda</td><td>{_member('Chada Suresh Reddy')}</td>"
        "<td rowspan='2'></td><td rowspan='2'><a href='/wiki/Telugu_Desam_Party'>Telugu Desam Party</a></td></tr>"
        f"<tr><th>39</th><td>Warangal</td><td>{_member('Bodakunti Venkateshwarlu')}</td></tr>"), 13)
    assert [(r.seat, r.party) for r in rows] == [("Hanamkonda", "Telugu Desam Party"),
                                                 ("Warangal", "Telugu Desam Party")]


def test_the_party_link_title_beats_the_short_visible_name():
    # 13th list: the page shows 'Janata Dal' but links Janata Dal (United).
    rows = ph.parse_wiki_members(_page(
        f"<tr><th>1</th><td>Bagaha</td><td>{_member('Mahendra Baitha')}</td>{_party('Janata Dal (United)', 'Janata Dal')}</tr>"), 13)
    assert rows[0].party == "Janata Dal (United)"


def test_a_by_election_gives_a_second_member_in_the_same_seat():
    # 14th list, Bobbili: one member died, a by-election winner of another party followed.
    rows = ph.parse_wiki_members(_page(
        f"<tr><th rowspan='2'>3</th><td rowspan='2'>Bobbili</td>"
        f"<td>{_member('Kondapalli Pydithalli Naidu', ' (Died on 18.8.2006)')}</td>{_party('Telugu Desam Party')}</tr>"
        f"<tr><td>{_member('Botsa Jhansi Lakshmi', ' (Elected on 7.12.2006)')}</td>{_party('Indian National Congress')}</tr>"), 14)
    assert [(r.seat, r.name, r.party) for r in rows] == [
        ("Bobbili", "Kondapalli Pydithalli Naidu", "Telugu Desam Party"),
        ("Bobbili", "Botsa Jhansi Lakshmi", "Indian National Congress")]


def test_a_vacant_row_gives_no_member():
    # 16th list, Ongole: a 'Vacant from' row spans the name and party columns.
    rows = ph.parse_wiki_members(_page(
        f"<tr><th rowspan='2'>16</th><td rowspan='2'>Ongole</td>"
        f"<td>{_member('Y. V. Subba Reddy', ' (resigned on 20 June 2018)')}</td>{_party('YSR Congress Party')}</tr>"
        "<tr><th colspan='3'><i>Vacant from 20 June 2018</i></th></tr>"), 16)
    assert [r.name for r in rows] == ["Y. V. Subba Reddy"]


def test_a_member_with_two_parties_keeps_the_first_as_the_party():
    # 17th list, Machilipatnam: the member cell spans two party rows.
    rows = ph.parse_wiki_members(_page(
        f"<tr><th rowspan='2'>11</th><td rowspan='2'>Machilipatnam</td>"
        f"<td rowspan='2'>{_member('Vallabhaneni Balashowry')}</td>{_party('YSR Congress Party')}</tr>"
        f"<tr>{_party('Jana Sena Party')}</tr>"), 17)
    assert len(rows) == 1
    assert rows[0].party == "YSR Congress Party"
    assert rows[0].parties == ["YSR Congress Party", "Jana Sena Party"]


def test_a_name_with_no_article_link_is_still_read():
    # 13th list, Assam: some names are plain text.
    rows = ph.parse_wiki_members(_page(
        f"<tr><th>4</th><td>Dhubri</td><td>Abdul Hamid\n</td>{_party('Indian National Congress')}</tr>"), 13)
    assert (rows[0].name, rows[0].title) == ("Abdul Hamid", "")


def test_a_two_row_header_under_a_party_key_row_is_read():
    # 16th list, Tamil Nadu: a party key row, then a two-row header.
    header = ("<tr><th colspan='6'>AIADMK (36) BJP (1)</th></tr>"
              "<tr><th colspan='3'>Constituency</th><th rowspan='2'>Elected member</th>"
              "<th colspan='2' rowspan='2'>Political party</th></tr>"
              "<tr><th>No.</th><th>Name</th><th>Reservation</th></tr>")
    rows = ph.parse_wiki_members(_page(
        f"<tr><td>1</td><td>Thiruvallur</td><td>SC</td><td>{_member('P. Venugopal')}</td>"
        f"{_party('All India Anna Dravida Munnetra Kazhagam')}</tr>", header=header, state="Tamil Nadu"), 16)
    assert [(r.seat, r.name, r.party) for r in rows] == [
        ("Thiruvallur", "P. Venugopal", "All India Anna Dravida Munnetra Kazhagam")]


def test_a_redirect_title_becomes_the_article_title():
    rows = ph.parse_wiki_members(_page(
        f"<tr><th>1</th><td>Bankura</td><td>{_member('Acharia Basudeb')}</td>{_party('Communist Party of India (Marxist)')}</tr>"),
        14, redirects={"Acharia Basudeb": "Basudeb Acharia"})
    assert rows[0].title == "Basudeb Acharia"


# --- names --------------------------------------------------------------------------------------

@pytest.mark.parametrize("a, b", [
    ("Raja A", "A. Raja"),
    ("Lal Krishna Advani", "L. K. Advani"),
    ("Kinjarapu Rammohan Naidu", "Ram Mohan Naidu Kinjarapu"),
    ("E. Ahamed", "E. Ahammed"),
    ("Dr. S Jagathratchakan", "S. Jagathrakshakan"),
])
def test_spellings_of_one_name_match(a, b):
    assert ph.name_score(a, b) > 0


@pytest.mark.parametrize("a, b", [
    ("Rajnath Singh", "Raghuvansh Singh"),
    ("Sonia Gandhi", "Rahul Gandhi"),
])
def test_different_names_do_not_match(a, b):
    assert ph.name_score(a, b) == 0


def test_close_spellings_of_different_names_can_match():
    # Known limit: 'Lakshman' and 'Lakhan' pair, so a tie keeps nothing.
    assert ph.name_score("Lakshman Singh", "Ram Lakhan Singh") > 0


def test_a_single_shared_word_with_a_leftover_word_is_weak():
    # sansad.in writes 'Delkar, Shri Mohan S.'. Only 'Mohan' pairs with 'Mohan Singh'.
    assert ph.name_match("Delkar, Shri Mohan S.", "Mohan Singh") == (1, 1)


def test_shared_word_ignores_common_name_words_and_finds_joined_spellings():
    assert ph.shares_a_word("D Ravi Kumar", "Durai Ravikumar")
    assert ph.shares_a_word("Sougata Ray", "Saugata Roy")
    assert not ph.shares_a_word("Pradeep Yadav", "Brij Bhushan Sharan Singh")
    assert not ph.shares_a_word("Virendra Singh", "Kalyan Singh")


def test_seat_names_compare_loosely():
    assert ph.same_seat("Peddapalle (SC)", "Peddapalli")
    assert not ph.same_seat("Kolar", "Koppal")


# --- matching -----------------------------------------------------------------------------------

def _member_row(mpsno, name, last=18, seat=None):
    return {"mpsno": mpsno, "mpFirstLastName": name, "lastLoksabha": last, "constName": seat}


def _wiki(name, seat, party="X", term=14, title=None):
    return ph.WikiRow(term=term, state="S", seat=seat, name=name, title=title or name, party=party, parties=[party])


def test_a_tie_between_two_rows_keeps_nothing():
    members = [_member_row(1, "Singh R")]
    rows = [_wiki("Rajnath Singh", "A"), _wiki("Raghuvansh Singh", "B")]
    matches, rejected = ph.match_term(members, rows, 14)
    assert matches == []
    assert rejected[0]["reason"] == "tie between wikipedia rows"


def test_one_article_in_two_rows_is_one_person():
    # 13th list: Sonia Gandhi won two seats in 1999.
    members = [_member_row(130, "Sonia Gandhi")]
    rows = [_wiki("Sonia Gandhi", "Bellary", "INC"), _wiki("Sonia Gandhi", "Amethi", "INC")]
    matches, _ = ph.match_term(members, rows, 13)
    assert [(m.mpsno, m.row.seat) for m in matches] == [(130, "Bellary")]


def test_in_the_last_term_a_different_seat_blocks_the_match():
    members = [_member_row(7, "A. Kumar", last=14, seat="Kolar")]
    rows = [_wiki("A. Kumar", "Koppal")]
    matches, _ = ph.match_term(members, rows, 14)
    assert matches == []


def test_in_the_last_term_the_right_seat_wins_a_name_tie():
    members = [_member_row(7, "Ajit Singh", last=14, seat="Baghpat")]
    rows = [_wiki("Ajit Singh", "Baghpat", title="Ajit Singh (politician)"), _wiki("Ajit Kumar Singh", "Other")]
    matches, _ = ph.match_term(members, rows, 14)
    assert [(m.row.seat, m.method) for m in matches] == [("Baghpat", "name+seat")]


def test_an_article_on_two_members_keeps_only_seat_confirmed_matches():
    # 13th list links G. Mallikarjunappa to the article of his son G. M. Siddeshwara.
    father = ph.Match(232, _wiki("G. Mallikarjunappa", "Davanagere", term=13, title="G. M. Siddeshwara"), "name+seat", 2)
    son_14 = ph.Match(3977, _wiki("G. M. Siddeshwara", "Davanagere", term=14), "name", 1)
    son_17 = ph.Match(3977, _wiki("G. M. Siddeshwara", "Davanagere", term=17), "name+seat", 1)
    kept, dropped, bad = ph.check_articles([father, son_14, son_17])
    assert kept == [father, son_17]
    assert [d["term"] for d in dropped] == [14]
    assert bad == {"G. M. Siddeshwara"}


def test_seat_fill_needs_a_shared_word():
    # 13th list, Gonda: the free row is the general election winner. Pradeep Yadav won the
    # by-election, and the page has no row for him.
    members = {13: [_member_row(1, "Pradeep Yadav", last=13, seat="Gonda"),
                    _member_row(2, "Sougata Ray", last=13, seat="Dum Dum")]}
    rows = {13: [_wiki("Brij Bhushan Sharan Singh", "Gonda", term=13), _wiki("Saugata Roy", "Dum Dum", term=13)]}
    added = ph.fill_by_seat([], members, rows)
    assert [(m.mpsno, m.row.name, m.method) for m in added] == [(2, "Saugata Roy", "seat")]


def test_article_fill_uses_the_article_from_another_term():
    rows = {13: [_wiki("Dr. Ramlakhan Singh", "Bhind", term=13, title="Ram Lakhan Singh")],
            14: [_wiki("Ram Lakhan Singh", "Bhind", term=14)]}
    members = {13: [_member_row(431, "Ram Lakhan Singh", last=14)], 14: [_member_row(431, "Ram Lakhan Singh", last=14)]}
    done = [ph.Match(431, rows[14][0], "name", 2)]
    added = ph.fill_by_article(done, members, rows)
    assert [(m.mpsno, m.row.term, m.method) for m in added] == [(431, 13, "article")]


# --- the real pages -----------------------------------------------------------------------------

def test_real_14th_list_gives_a_raja_his_term_14_seat_and_party():
    # sansad.in gives A. Raja only his term 18 seat (Nilgiris). In term 14 he sat for Perambalur.
    # Only Tamil Nadu is matched, to keep the test fast.
    redirects = json.loads((RAW / "wiki_redirects.json").read_text(encoding="utf-8"))
    members = json.loads((RAW / "sansad_ls14.json").read_text(encoding="utf-8"))
    rows = ph.parse_wiki_members((RAW / "wiki_ls14.html").read_text(encoding="utf-8"), 14, redirects)
    assert len({(r.state, r.seat) for r in rows}) >= 543
    tn_members = [m for m in members if m["stateName"] == "Tamil Nadu"]
    tn_rows = [r for r in rows if r.state == "Tamil Nadu"]
    assert len(tn_rows) >= 39
    matches, _ = ph.match_term(tn_members, tn_rows, 14)
    raja = [m for m in matches if m.mpsno == 344]
    assert [(m.row.seat, m.row.party) for m in raja] == [("Perambalur", "Dravida Munnetra Kazhagam")]
    assert len(matches) >= 35


def test_one_person_with_two_sansad_codes_keeps_both_seat_confirmed_matches():
    # sansad.in gives Bhaskarrao Patil of Nanded code 315 (term 13) and code 4375 (term 15).
    a = ph.Match(315, _wiki("Bhaskarrao Patil", "Nanded", term=13, title="Bhaskarrao Bapurao Khatgaonkar Patil"), "seat", 0)
    b = ph.Match(4375, _wiki("Bhaskarrao Patil", "Nanded", term=15, title="Bhaskarrao Bapurao Khatgaonkar Patil"), "name+seat", 3)
    kept, dropped, _ = ph.check_articles([a, b])
    assert kept == [a, b]
    assert dropped == []


# --- the hand-filled file -----------------------------------------------------------------------

def _terms_row(term, mpsno):
    return {"term": term, "mpsno": mpsno, "method": "none", "score": "", "party": "", "constituency": ""}


def test_manual_file_fills_a_row_with_no_party(tmp_path, monkeypatch):
    from scripts import build_party_history as b
    f = tmp_path / "manual.tsv"
    f.write_text("term\tmpsno\tname\tparty\tconstituency\tnote\n"
                 "13\t3960\tH.D. Devegowda\tJD(S)\tKanakapura\t\n"
                 "13\t563\tPrabodh Panda\t\t\t\n", encoding="utf-8")
    monkeypatch.setattr(b, "MANUAL", f)
    rows = [_terms_row(13, 3960), _terms_row(13, 563)]
    b.apply_manual(rows, {"janatadalsecular": "JD(S)"})
    assert (rows[0]["method"], rows[0]["party"], rows[0]["constituency"]) == ("manual", "JD(S)", "Kanakapura")
    assert rows[1]["method"] == "none"


def test_manual_file_refuses_an_unknown_party_code(tmp_path, monkeypatch):
    from scripts import build_party_history as b
    f = tmp_path / "manual.tsv"
    f.write_text("term\tmpsno\tparty\n13\t3960\tJanata Dal Secular\n", encoding="utf-8")
    monkeypatch.setattr(b, "MANUAL", f)
    with pytest.raises(SystemExit):
        b.apply_manual([_terms_row(13, 3960)], {"janatadalsecular": "JD(S)"})

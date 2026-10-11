from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from functools import lru_cache
from difflib import SequenceMatcher
from urllib.parse import unquote

from bs4 import BeautifulSoup

from translit import fold


@dataclass
class WikiRow:
    # A seat with a by-election gives two rows.
    term: int
    state: str
    seat: str
    name: str          # the link text on the page
    title: str         # the Wikipedia article title, or "" for a name with no article
    party: str         # the first party in the row: the party at election time
    parties: list[str] = field(default_factory=list)  # every party the page shows for this member


# --- the table grid -------------------------------------------------------------------------

def table_grid(table) -> list[list]:
    # A cell with rowspan or colspan fills every grid position that it covers.
    grid: list[list] = []
    pending: dict[tuple[int, int], object] = {}
    for r, tr in enumerate(table.find_all("tr")):
        row: list = []
        c = 0
        cells = tr.find_all(["th", "td"], recursive=False)
        i = 0
        while i < len(cells) or (r, c) in pending:
            if (r, c) in pending:
                row.append(pending.pop((r, c)))
                c += 1
                continue
            cell = cells[i]
            i += 1
            rs = _span(cell.get("rowspan"))
            cs = _span(cell.get("colspan"))
            for dc in range(cs):
                row.append(cell)
                for dr in range(1, rs):
                    pending[(r + dr, c + dc)] = cell
            c += cs
        grid.append(row)
    return grid


def _span(value) -> int:
    m = re.match(r"\d+", str(value or "1"))
    return max(1, int(m.group())) if m else 1


def _text(cell) -> str:
    if cell is None:
        return ""
    for sup in cell.find_all("sup"):
        sup.extract()
    return re.sub(r"\s+", " ", cell.get_text(" ", strip=True)).strip()


def _person_link(cell):
    for a in cell.find_all("a", href=True):
        href = a["href"]
        if href.startswith("/wiki/") and ":" not in href[6:]:
            return a
        if "redlink=1" in href:
            return a
    return None


def _title_of(a) -> str:
    href = a["href"]
    if href.startswith("/wiki/"):
        return unquote(href[6:]).replace("_", " ")
    return ""  # a page that does not exist yet (red link)


def _header(grid: list[list]) -> tuple[list[str], int]:
    # Header rows are the leading rows with only <th> cells. A one-cell row that spans the table is a party key, not a header.
    labels = [""] * max((len(r) for r in grid), default=0)
    first = 0
    for r, row in enumerate(grid):
        if not row or any(c.name != "th" for c in row):
            break
        first = r + 1
        if len({id(c) for c in row}) == 1 and len(row) > 1:
            continue
        for i, c in enumerate(row):
            t = _text(c).lower()
            if t and t not in labels[i]:
                labels[i] = (labels[i] + " " + t).strip()
    return labels, first


def _columns(labels: list[str]) -> tuple[int | None, int | None, list[int]]:
    seat = next((i for i, h in enumerate(labels) if "constituency" in h and "name" in h), None)
    if seat is None:
        seat = next((i for i, h in enumerate(labels) if "constituency" in h), None)
    member = next((i for i, h in enumerate(labels)
                   if i != seat and "constituency" not in h
                   and any(w in h for w in ("name", "member", "m.p."))), None)
    party = [i for i, h in enumerate(labels) if "party" in h and "alliance" not in h]
    return seat, member, party


def parse_wiki_members(html: str, term: int, redirects: dict[str, str] | None = None) -> list[WikiRow]:
    """`redirects` maps a link title to the article that it redirects to."""
    redirects = redirects or {}
    soup = BeautifulSoup(html, "html.parser")
    rows: list[WikiRow] = []
    for table in soup.find_all("table"):
        grid = table_grid(table)
        if not grid:
            continue
        labels, first = _header(grid)
        seat_col, name_col, party_cols = _columns(labels)
        if seat_col is None or name_col is None or not party_cols:
            continue
        state = _state_before(table)
        by_member: dict[int, WikiRow] = {}
        for grow in grid[first:]:
            if len(grow) <= max(name_col, seat_col):
                continue
            cell = grow[name_col]
            if cell is grow[seat_col]:
                continue  # a "Vacant" row that spans the seat and name columns
            link = _person_link(cell)
            if link is not None:
                name, title, key = _text(link), _title_of(link), id(link)
                title = redirects.get(title, title)
            else:  # a name with no article link, or an empty seat
                name, title, key = re.sub(r"\(.*?\)", " ", _text(cell)).strip(), "", id(cell)
                if not name or name.lower().startswith("vacant"):
                    continue
            party = _party(grow, party_cols, redirects)
            if key in by_member:  # a member cell that spans two rows: a change of party
                if party and party not in by_member[key].parties:
                    by_member[key].parties.append(party)
                continue
            row = WikiRow(
                term=term, state=state, seat=clean_seat(_text(grow[seat_col])),
                name=name, title=title, party=party,
                parties=[party] if party else [],
            )
            by_member[key] = row
            rows.append(row)
    return rows


def _party(grow: list, party_cols: list[int], redirects: dict[str, str]) -> str:
    # Prefer the article title of the party link. The visible text is often short: the 13th list shows "Janata Dal" for Janata Dal (United).
    for i in party_cols:
        if i >= len(grow):
            continue
        for a in grow[i].find_all("a", href=True):
            if a["href"].startswith("/wiki/") and ":" not in a["href"][6:]:
                t = _title_of(a)
                return redirects.get(t, t)
    return next((t for t in (_text(grow[i]) for i in party_cols if i < len(grow)) if t), "")


def party_titles(html: str) -> set[str]:
    out: set[str] = set()
    soup = BeautifulSoup(html, "html.parser")
    for table in soup.find_all("table"):
        grid = table_grid(table)
        if not grid:
            continue
        labels, first = _header(grid)
        _, _, party_cols = _columns(labels)
        for grow in grid[first:]:
            p = _party(grow, party_cols, {})
            if p:
                out.add(p)
    return out


def _state_before(table) -> str:
    h = table.find_previous(["h2", "h3"])
    if h is None:
        return ""
    return re.sub(r"\[edit\]", "", h.get_text(" ", strip=True)).strip()


def clean_seat(text: str) -> str:
    return re.sub(r"\s*\((?:SC|ST)\)\s*", " ", text).strip()


# --- name matching --------------------------------------------------------------------------

HONORIFICS = {
    "shri", "sri", "smt", "shrimati", "kumari", "km", "dr", "prof", "adv", "advocate",
    "mr", "mrs", "ms", "col", "retd", "capt", "major", "gen", "lt", "sardar", "dr.",
    "thiru", "tmt", "selvi", "kunwar", "kunwari", "rajkumari", "maharani", "raja",
}
# "raja" is a title for some members and a name for others (A. Raja). name_tokens drops it only when other full words remain.


@lru_cache(maxsize=None)
def name_tokens(name: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    s = unicodedata.normalize("NFKD", name)
    s = "".join(ch for ch in s if not unicodedata.combining(ch)).lower()
    s = re.sub(r"\(.*?\)", " ", s)
    words = [w for w in re.split(r"[^a-z]+", s) if w]
    full = [w for w in words if len(w) > 1]
    initials = [w for w in words if len(w) == 1]
    kept = [w for w in full if w not in HONORIFICS]
    if kept:
        full = kept
    return tuple(full), tuple(initials)


@lru_cache(maxsize=None)
def _same_word(a: str, b: str) -> bool:
    if a == b:
        return True
    fa, fb = fold(a), fold(b)
    if fa == fb:
        return True
    return min(len(fa), len(fb)) >= 4 and SequenceMatcher(None, fa, fb).ratio() >= 0.8


def name_score(a: str, b: str) -> int:
    """0 means the names cannot be one person."""
    return name_match(a, b)[0]


@lru_cache(maxsize=None)
def name_match(a: str, b: str) -> tuple[int, int]:
    """Return (score, leftover). Score is the count of full words that pair with full words, 0 for no match. Leftover is the count of unpaired full words in the longer name."""
    fa, ia = name_tokens(a)
    fb, ib = name_tokens(b)
    if not fa or not fb:
        return 0, 0
    short, long_ = ((fa, ia), (fb, ib)) if len(fa) + len(ia) <= len(fb) + len(ib) else ((fb, ib), (fa, ia))
    long_full = list(long_[0])
    long_init = list(long_[1])
    score = 0
    for w in short[0]:
        hit = next((x for x in long_full if _same_word(w, x)), None)
        if hit is not None:
            long_full.remove(hit)
            score += 1
            continue
        if w[0] in long_init:
            long_init.remove(w[0])
            continue
        return 0, 0
    for ch in short[1]:
        if ch in long_init:
            long_init.remove(ch)
            continue
        hit = next((x for x in long_full if x[0] == ch), None)
        if hit is not None:
            long_full.remove(hit)
            continue
        return 0, 0
    return score, len(long_full)


@lru_cache(maxsize=None)
def seat_key(seat: str) -> str:
    words = re.split(r"[^a-z]+", clean_seat(seat).lower())
    return "".join(fold(w) for w in words if w)


@lru_cache(maxsize=None)
def same_seat(a: str, b: str) -> bool:
    ka, kb = seat_key(a), seat_key(b)
    if not ka or not kb:
        return False
    return ka == kb or SequenceMatcher(None, ka, kb).ratio() >= 0.8


# --- matching one term ----------------------------------------------------------------------

@dataclass
class Match:
    mpsno: int
    row: WikiRow
    method: str   # name, name+seat, article
    score: int


def _pair_score(member: dict, row: WikiRow, seat_known: bool) -> int:
    # With no seat to confirm the pair, a score of 1 with a leftover word is too weak: "Mohan S. Delkar" against "Mohan Singh" pairs only "Mohan".
    name = member["mpFirstLastName"] or ""
    best = 0
    for other in (row.name, row.title):
        if not other:
            continue
        score, leftover = name_match(name, other)
        if score == 1 and leftover and not seat_known:
            score = 0
        best = max(best, score)
    return best


def _seat_ok(member: dict, row: WikiRow, term: int) -> bool | None:
    # sansad.in gives the seat of the member's last term only. Returns None when the seat is unknown.
    if member.get("lastLoksabha") != term or not member.get("constName"):
        return None
    return same_seat(member["constName"], row.seat)


def match_term(members: list[dict], rows: list[WikiRow], term: int) -> tuple[list[Match], list[dict]]:
    """Keep a pair only when each side is the other's single best candidate. A tie keeps nothing. Returns the kept matches and the rejected pairs with a reason."""
    rejected: list[dict] = []
    scores: dict[tuple[int, int], int] = {}
    for m in members:
        for j, r in enumerate(rows):
            ok = _seat_ok(m, r, term)
            if ok is False:
                continue
            s = _pair_score(m, r, seat_known=bool(ok))
            if s <= 0:
                continue
            scores[(m["mpsno"], j)] = s + (10 if ok else 0)

    best_for_member = _best({(mp, j): s for (mp, j), s in scores.items()})
    best_for_row = _best({(j, mp): s for (mp, j), s in scores.items()})

    matches: list[Match] = []
    by_no = {m["mpsno"]: m for m in members}
    for mp, js in best_for_member.items():
        titles = {rows[j].title for j in js}
        if len(js) > 1 and len(titles) == 1 and "" not in titles:
            # One article in two rows: two seats or a by-election. Keep the first row and every party.
            first = rows[min(js)]
            for j in sorted(js)[1:]:
                for p in rows[j].parties:
                    if p not in first.parties:
                        first.parties.append(p)
            js = [min(js)]
        if len(js) != 1:
            rejected.append({"term": term, "mpsno": mp, "reason": "tie between wikipedia rows",
                             "detail": "; ".join(rows[j].name for j in js)})
            continue
        j = js[0]
        if best_for_row.get(j) != [mp]:
            others = best_for_row.get(j, [])
            rejected.append({"term": term, "mpsno": mp, "reason": "wikipedia row prefers another member",
                             "detail": rows[j].name + " <- " + "; ".join(by_no[o]["mpFirstLastName"] for o in others)})
            continue
        s = scores[(mp, j)]
        matches.append(Match(mp, rows[j], "name+seat" if s >= 10 else "name", s % 10))
    return matches, rejected


def _best(scores: dict[tuple[int, int], int]) -> dict[int, list[int]]:
    """Two or more values for a key mean a tie."""
    top: dict[int, int] = {}
    for (k, _), s in scores.items():
        top[k] = max(top.get(k, s), s)
    best: dict[int, list[int]] = {}
    for (k, v), s in sorted(scores.items()):
        if s == top[k]:
            best.setdefault(k, []).append(v)
    return best


def check_articles(matches: list[Match]) -> tuple[list[Match], list[dict], set[str]]:
    # One article is one person, so two codes on one article mean a wrong match. Only seat-confirmed matches stay.
    # Two seat-confirmed codes can be one person with two sansad.in codes (Bhaskarrao Patil of Nanded: 315 and 4375).
    codes: dict[str, set[int]] = {}
    for m in matches:
        if m.row.title:
            codes.setdefault(m.row.title, set()).add(m.mpsno)
    bad = {t for t, c in codes.items() if len(c) > 1}
    kept, dropped = [], []
    for m in matches:
        t = m.row.title
        if t in bad and m.method not in ("name+seat", "seat"):
            dropped.append({"term": m.row.term, "mpsno": m.mpsno, "reason": "article matches two members",
                            "detail": t + " <- " + ", ".join(map(str, sorted(codes[t])))})
        else:
            kept.append(m)
    return kept, dropped, bad


def fill_by_article(matches: list[Match], members_by_term: dict[int, list[dict]],
                    rows_by_term: dict[int, list[WikiRow]], bad: set[str] = frozenset()) -> list[Match]:
    # If a member matched article A in one term, and one unclaimed row in another term links A, that row is the member. The name spelling does not matter.
    article_of: dict[int, set[str]] = {}
    for m in matches:
        if m.row.title and m.row.title not in bad:
            article_of.setdefault(m.mpsno, set()).add(m.row.title)
    done = {(m.row.term, m.mpsno) for m in matches}
    claimed = {(m.row.term, id(m.row)) for m in matches}
    added: list[Match] = []
    for term, members in members_by_term.items():
        free = [r for r in rows_by_term[term] if (term, id(r)) not in claimed and r.title]
        by_title: dict[str, list[WikiRow]] = {}
        for r in free:
            by_title.setdefault(r.title, []).append(r)
        users: dict[str, list[int]] = {}
        for mem in members:
            if (term, mem["mpsno"]) in done:
                continue
            titles = article_of.get(mem["mpsno"], set())
            if len(titles) != 1:
                continue
            t = next(iter(titles))
            if len(by_title.get(t, [])) == 1:
                users.setdefault(t, []).append(mem["mpsno"])
        for t, mps in users.items():
            if len(mps) == 1:
                added.append(Match(mps[0], by_title[t][0], "article", 0))
    return added


def fill_by_seat(matches: list[Match], members_by_term: dict[int, list[dict]],
                 rows_by_term: dict[int, list[WikiRow]]) -> list[Match]:
    # Last term only. One unclaimed row in the seat with a shared name word is the member. This pairs "Sougata Ray" with "Saugata Roy".
    done = {(m.row.term, m.mpsno) for m in matches}
    claimed = {(m.row.term, id(m.row)) for m in matches}
    added: list[Match] = []
    for term, members in members_by_term.items():
        free = [r for r in rows_by_term[term] if (term, id(r)) not in claimed]
        users: dict[int, list[int]] = {}
        for mem in members:
            if (term, mem["mpsno"]) in done or mem.get("lastLoksabha") != term or not mem.get("constName"):
                continue
            hits = [r for r in free if same_seat(mem["constName"], r.seat)]
            if len(hits) == 1 and (shares_a_word(mem["mpFirstLastName"] or "", hits[0].name)
                                   or shares_a_word(mem["mpFirstLastName"] or "", hits[0].title)):
                users.setdefault(id(hits[0]), []).append(mem["mpsno"])
        rows = {id(r): r for r in free}
        for rid, mps in users.items():
            if len(mps) == 1:
                added.append(Match(mps[0], rows[rid], "seat", 0))
    return added


# Words that many unrelated members share. They are no evidence that two names are one person.
COMMON_NAME_WORDS = {
    "singh", "kumar", "kumari", "patel", "patil", "yadav", "devi", "ram", "lal", "prasad", "rao",
    "reddy", "bhai", "ben", "sharma", "mohammed", "mohammad", "md", "shri", "chandra", "babu",
}


def shares_a_word(a: str, b: str) -> bool:
    # A word also counts inside a joined spelling: "Ravikumar" contains "Ravi".
    if not a or not b:
        return False
    wa = [w for w in name_tokens(a)[0] if w not in COMMON_NAME_WORDS]
    wb = [w for w in name_tokens(b)[0] if w not in COMMON_NAME_WORDS]
    ja, jb = "".join(name_tokens(a)[0]), "".join(name_tokens(b)[0])
    for x in wa:
        if any(_same_word(x, y) for y in wb) or (len(x) >= 4 and x in jb):
            return True
    return any(len(y) >= 4 and y in ja for y in wb)

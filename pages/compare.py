"""The compare page: two members or two parties side by side, as JSON.

Route: /compare?kind=member|party&a=<key>&b=<key>. A member key is persons.id. A party key is parties.code.
Optional query argument terms: a comma list of Lok Sabha numbers, for example terms=17,18.
Without terms, the page uses the terms in which both sides have tagged speeches.
Missing or unknown keys, or a kind that is not member or party, give None.

Each side has a share: the tagged speeches of the side with a subject, divided by all tagged speeches of the side in the terms.
The comparison shows salience only. It never shows support or opposition.
"""
from collections import Counter

from sqlalchemy import text

from pages.common import slug
from pages.member import member_tag_rows
from pages.party import SUBJECT_KINDS, corpus, find_party, general_tags, party_counts, TERMS

MIN_N = {"member": 3, "party": 10}   # least speeches on a subject for a side to count it
RATIO = 2.0                          # a subject is distinctive when one share is at least 2 times the other
GENERAL_SHARE = 0.03                 # more than 3% of all tagged speeches in the same terms: general
TOP = 8


def parse_terms(raw):
    """Return a sorted list of valid Lok Sabha numbers from a comma list, or None when raw is empty or bad."""
    if not raw:
        return None
    try:
        out = sorted({int(x) for x in str(raw).split(",") if x.strip()})
    except ValueError:
        return None
    out = [t for t in out if t in TERMS]
    return out or None


def compare_sides(tags, hidden, all_cnt, all_n, ca, na, cb, nb, min_n):
    """Compare two sides. ca and cb are Counters of tag id to tagged speeches. na and nb are the tagged speeches.

    The order of each list follows a stated rule. shared: the lower of the two shares, high first.
    only_a: share of a minus share of b, high first. only_b: the same for b.
    mirror: the largest of the two shares, high first. Ties break by tag name.
    """
    general = general_tags(all_cnt, all_n, GENERAL_SHARE) | hidden if all_n else set(hidden)

    def share(cnt, tid, n):
        return cnt[tid] / n if n else 0.0

    def item(tid):
        t = tags[tid]
        return {"tag": t["tag"], "slug": slug(t["tag"]), "type": t["type"],
                "a_n": ca[tid], "a_share": round(share(ca, tid, na), 4),
                "b_n": cb[tid], "b_share": round(share(cb, tid, nb), 4)}

    shared, only_a, only_b = [], [], []
    for tid in set(ca) | set(cb):
        t = tags[tid]
        if tid in general or t["type"] not in SUBJECT_KINDS:
            continue
        sa, sb = share(ca, tid, na), share(cb, tid, nb)
        if ca[tid] >= min_n and cb[tid] >= min_n and max(sa, sb) < RATIO * min(sa, sb):
            shared.append(item(tid))
        elif ca[tid] >= min_n and sa >= RATIO * sb:
            only_a.append(item(tid))
        elif cb[tid] >= min_n and sb >= RATIO * sa:
            only_b.append(item(tid))
    shared.sort(key=lambda r: (-min(r["a_share"], r["b_share"]), r["tag"]))
    only_a.sort(key=lambda r: (-(r["a_share"] - r["b_share"]), r["tag"]))
    only_b.sort(key=lambda r: (-(r["b_share"] - r["a_share"]), r["tag"]))
    mirror = sorted(shared[:6] + only_a[:4] + only_b[:4], key=lambda r: (-max(r["a_share"], r["b_share"]), r["tag"]))

    def topshare(cnt, n):
        ok = [(v, tags[t]["tag"], t) for t, v in cnt.items()
              if t not in general and tags[t]["type"] in SUBJECT_KINDS and v >= min_n]
        ok.sort(key=lambda x: (-x[0], x[1]))
        return [{"tag": name, "slug": slug(name), "n": v, "share": round(v / n, 4)} for v, name, _ in ok[:3]]

    return {"shared": shared[:TOP], "only_a": only_a[:TOP], "only_b": only_b[:TOP], "mirror": mirror,
            "n_shared": len(shared), "n_only_a": len(only_a), "n_only_b": len(only_b),
            "top_a": topshare(ca, na), "top_b": topshare(cb, nb)}


def _member_side(conn, key):
    try:
        pid = int(key)
    except (TypeError, ValueError):
        return None
    pe = conn.execute(text("SELECT id, name FROM persons WHERE id = :p"), {"p": pid}).mappings().first()
    if pe is None:
        return None
    rows = member_tag_rows(conn, pe["id"])
    by_term_sp, by_term_cnt = {}, {}
    for sp, term, tid in rows:
        by_term_sp.setdefault(term, set()).add(sp)
        by_term_cnt.setdefault(term, Counter())[tid] += 1
    return {"info": {"id": pe["id"], "name": pe["name"], "_pid": pe["id"]},
            "sp": {t: len(v) for t, v in by_term_sp.items()}, "cnt": by_term_cnt}


def _party_side(conn, key):
    party = find_party(conn, key)
    if party is None:
        return None
    p_cnt, p_sp, _, _, _ = party_counts(conn, party)
    return {"info": {"id": party["code"], "name": party["name"]},
            "sp": {t: n for t, n in p_sp.items() if n}, "cnt": p_cnt}


def _member_extra(conn, pid, terms):
    r = conn.execute(text("""
        SELECT string_agg(DISTINCT sp.constituency, ', ') AS seat, string_agg(DISTINCT p.code, ', ') AS party
        FROM speakers sp LEFT JOIN parties p ON p.id = sp.party_id
        WHERE sp.person_id = :p AND sp.lok_sabha_term = ANY(:t)"""), {"p": pid, "t": list(terms)}).mappings().one()
    return {"seat": r["seat"], "party": r["party"]}


def compare_page(conn, args=None):
    args = args or {}
    kind, ka, kb = args.get("kind"), args.get("a"), args.get("b")
    if kind not in MIN_N or not ka or not kb:
        return None
    side = _member_side if kind == "member" else _party_side
    sa, sb = side(conn, ka), side(conn, kb)
    if sa is None or sb is None:
        return None
    tags, by_term_all, all_n, hidden = corpus(conn)
    terms = parse_terms(args.get("terms"))
    if terms is None:
        terms = sorted(set(sa["sp"]) & set(sb["sp"]))
    ca, cb, all_cnt = Counter(), Counter(), Counter()
    for t in terms:
        ca.update(sa["cnt"].get(t, {}))
        cb.update(sb["cnt"].get(t, {}))
        all_cnt.update(by_term_all.get(t, {}))
    na = sum(sa["sp"].get(t, 0) for t in terms)
    nb = sum(sb["sp"].get(t, 0) for t in terms)
    n_all = sum(all_n.get(t, 0) for t in terms)
    out = {"kind": kind, "terms": terms, "min_n": MIN_N[kind], "ratio": RATIO, "general_share": GENERAL_SHARE,
           "tagged_all": n_all, "a_tagged": na, "b_tagged": nb}
    out.update(compare_sides(tags, hidden, all_cnt, n_all, ca, na, cb, nb, MIN_N[kind]))
    for key, s in (("a", sa), ("b", sb)):
        info = dict(s["info"])
        pid = info.pop("_pid", None)
        if pid is not None:
            info.update(_member_extra(conn, pid, terms) if terms else {"seat": None, "party": None})
        out[key] = info
    if kind == "party":
        out["parties"] = party_choices(conn)
    out["counts_note"] = (
        "tagged_all counts the tagged speeches of all members in terms. a_tagged and b_tagged count the tagged speeches "
        "of each side in terms. For a party, a speech belongs to the party of the member at the date of the debate. "
        "In shared, only_a, only_b, mirror, a_n and b_n count the tagged speeches of each side with the tag. "
        "a_share is a_n divided by a_tagged, and b_share is b_n divided by b_tagged. In top_a and top_b, n counts "
        "the side's tagged speeches with the tag and share is n divided by that side's tagged speeches. "
        "n_shared, n_only_a and n_only_b count the tags in each list before the cut to the top 8. "
        "In parties, n counts the distinct members who ever had the party. "
        "A tag is general when it is on more than general_share of tagged_all, and general tags are left out.")
    return out


def party_choices(conn):
    """Return the 30 parties with the most distinct members, most members first, for a picker. n counts members."""
    return [dict(r) for r in conn.execute(text("""
        SELECT p.code, p.name, count(DISTINCT sp.person_id) AS n FROM parties p JOIN speakers sp ON sp.party_id = p.id
        GROUP BY 1, 2 ORDER BY n DESC, p.code LIMIT 30""")).mappings()]


ROUTES = [("/compare", compare_page)]

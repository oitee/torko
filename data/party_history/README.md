# Party history

This folder gives each member a party and a constituency for each Lok Sabha term, from the 13th to the 18th.

sansad.in gives the party and the constituency for a member's last term only. Before this step, Torko showed that last-term party for the whole career of a member. A speech that a member gave as an INC member in 2004 showed the party that the member had joined by 2019.

## Sources

| File | Source | What it gives |
|---|---|---|
| `raw/sansad_ls<N>.json` | `sansad.in/api_ls/member?loksabha=N` | Each member who sat in term N, with the member code. Its party and constituency fields are for the member's last term, not for term N. Contact details are not kept. |
| `raw/wiki_ls<N>.html` | Wikipedia, "List of members of the Nth Lok Sabha" | Seat, member name, and party for each seat in term N. The first line holds the page revision id. |
| `raw/wiki_redirects.json` | Wikipedia API | Link title to article title. One person can have links under two titles. |
| `party_codes.tsv` | Written by hand | Wikipedia party names that the sansad.in data cannot map to a party code. An empty code means that the party is not known. |

## Steps

```bash
python3 -I scripts/fetch_party_sources.py       # network: writes raw/
python3 -I scripts/build_party_history.py       # no network, no database: writes results/
python3 -m scripts.load_party_history           # database: one speakers row for each (member, term)
```

`results/speaker_terms.tsv` has one row for each (member, term) pair on the sansad.in lists: 3,385 rows. `results/report.md` gives the counts. `results/rejects.tsv` lists the pairs that the matcher refused.

## How a member is matched to a Wikipedia row

1. The matcher compares names only inside one term. A term has about 560 members, not the 5,000 of all terms.
2. A pair is kept only when each side is the other's single best candidate. A tie keeps nothing.
3. In the member's last term, sansad.in knows the seat. A pair in a different seat is never kept.
4. One Wikipedia article is one person. If an article matches two member codes, only the matches with a confirmed seat stay.
5. A member with one article in other terms takes the free row with that article.
6. In the last term, a member takes the only free row in the sansad.in seat, if the two names share one word that is not a common name word, such as Singh or Kumar.

The `method` column records the rule that made each match: `name+seat`, `name`, `article`, or `seat`.

## Rules for the data

- **The party is the party at the election.** When Wikipedia shows two parties in one term, the first is the party, and `other_parties` holds the rest. A change of party inside a term is not shown anywhere else.
- **The last term keeps the sansad.in party.** The loader does not change that row.
- **The constituency is for matching and display only.** It is the Wikipedia spelling. Do not join on it, group by it, or compare it across terms. Spellings differ across sources, and seat boundaries changed with the delimitation orders of 1976 and 2008.
- **A miss is acceptable. A wrong person is not.** A member with no match gets a row with no party (`sansad-term-list`).

## Known faults

- Wikipedia does not list every by-election winner. The 13th list has about 25 members fewer than sansad.in.
- The Wikipedia list for the 18th term shows the party of today, not the party at the election. Torko does not use it, because the 18th term is the last term of all its members.
- sansad.in itself can be wrong for the last term. Example: it gives K. H. Muniyappa the seat Koppal and the party BJP for the 16th term. Wikipedia gives Kolar and INC.
- 56 (member, term) pairs speak in the debates but have no row: most are Rajya Sabha ministers, who are not Lok Sabha members. Their turns show no party for that term.

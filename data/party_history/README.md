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
| `party_changes.tsv` | Wikipedia cell notes, then a manual review | Each change of party inside a term: member, from party, to party, and the date. 27 rows. A by-election row has the date from the Wikipedia note. A defection row has no date yet. Made once from the notes, then edited by hand. |
| `party_events.tsv` | Written by hand from the manual review | The party at the election where a source was wrong (`kind` = election, no date), and each formal change inside a term with its date: by-election, split, merger, expulsion. The loader reads it. |
| `manual.tsv` | Filled by hand | The (member, term) pairs with no party after all rules, sorted by words spoken. Fill the `party` column with a known party code. The build refuses an unknown code. |

## Steps

```bash
python3 -I scripts/fetch_party_sources.py       # network: writes raw/
python3 -I scripts/build_party_history.py       # no network, no database: writes results/
python3 -m scripts.load_party_history           # database: one speakers row for each (member, term)
```

`results/speaker_terms.tsv` has one row for each (member, term) pair on the sansad.in lists: 3,385 rows. `results/report.md` gives the counts. `results/rejects.tsv` lists the pairs that the matcher refused. `results/last_term_disagreements.tsv` lists the last terms in which sansad.in and Wikipedia give different parties, with an empty `review` column.

The loader writes the party as an id into `speakers.party_id`. The table `parties` holds each code once, with its full name.

## How a member is matched to a Wikipedia row

1. The matcher compares names only inside one term. A term has about 560 members, not the 5,000 of all terms.
2. A pair is kept only when each side is the other's single best candidate. A tie keeps nothing.
3. In the member's last term, sansad.in knows the seat. A pair in a different seat is never kept.
4. One Wikipedia article is one person. If an article matches two member codes, only the matches with a confirmed seat stay.
5. A member with one article in other terms takes the free row with that article.
6. In the last term, a member takes the only free row in the sansad.in seat, if the two names share one word that is not a common name word, such as Singh or Kumar.
7. The article fill runs again, with the articles that the seat fill found.
8. A row in `manual.tsv` with a party replaces the result for that pair.

The `method` column records the rule that made each match: `name+seat`, `name`, `article`, `seat`, or `manual`.

## Rules for the data

- **The party follows the House record, with dates.** Each (member, term) has a first row from the first day of the term. A formal event in `party_events.tsv` adds a row from its date: a by-election, a split or merger that the House recognised, or an expulsion. A member who only works for another party keeps the party of the House record. A suspension changes nothing.
- **A speech takes the row that is true on the date of its debate.** The view `speaker_periods` gives each row the date on which the next row starts.
- **The last term starts from the sansad.in party.** A row of kind `election` in `party_events.tsv` replaces it where the manual review found it wrong. Each run of the loader first resets these rows to the sansad.in values, then applies the review.
- **A change after the last sitting of a term affects no speech.** Example: the last sitting of term 17 is on 2024-02-10, so a member who joined BJP in March 2024 needs no dated row.
- **The constituency is for matching and display only.** It is the Wikipedia spelling. Do not join on it, group by it, or compare it across terms. Spellings differ across sources, and seat boundaries changed with the delimitation orders of 1976 and 2008.
- **A miss is acceptable. A wrong person is not.** A member with no match gets a row with no party (`sansad-term-list`).
- **A speaker with no Lok Sabha seat in the term keeps the last-term party.** This is mostly a minister from the Rajya Sabha. The loader adds a row with source `last-term-fallback`, the party of the member's last-term row, and no constituency. TODO: a real party for speakers who are not Lok Sabha members.

## Known faults

- Wikipedia does not list every by-election winner. The 13th list has about 25 members fewer than sansad.in.
- A Wikipedia list does not always show the party at the election. The 17th list shows a later party for some members, for example BJP for Ravneet Singh Bittu, who won Ludhiana for INC in 2019.
- sansad.in can give one person two member codes. Example: Bhaskarrao Patil of Nanded has code 315 in term 13 and code 4375 in term 15.
- The Wikipedia list for the 18th term shows the party of today, not the party at the election. Torko does not use it, because the 18th term is the last term of all its members.
- Many dates in the Wikipedia cell notes are copies. On the 16th list, 21 members "died on 30 April 2019" and 32 members "resigned on 20 June 2018". Use a Wikipedia date only when a manual review confirms it.
- sansad.in itself can be wrong for the last term. Example: it gives K. H. Muniyappa the seat Koppal and the party BJP for the 16th term. Wikipedia gives Kolar and INC.

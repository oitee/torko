# Party history

This step gives each member a party and a constituency for each Lok Sabha term, from the 13th to the 18th. sansad.in gives only the party of the last term of a member. This step adds the party of each earlier term. It writes `speakers.party_id` and the table `parties`.

## How to run

Run from the repo root.

```bash
python3 -I scripts/fetch_party_sources.py       # network: writes raw/
python3 -I scripts/build_party_history.py       # no network, no database: writes results/
python3 -m scripts.load_party_history           # database: one speakers row for each (member, term)
```

None of the three scripts has a flag. The loader needs the database settings from `.env`. Each run of the loader first resets the last-term rows to the sansad.in values, then applies `party_events.tsv`.

## Files

| Path | What it is |
|---|---|
| `raw/sansad_ls<N>.json` | Members of term N from `sansad.in/api_ls/member?loksabha=N`, with the member code. Its party and constituency are for the last term, not for term N. |
| `raw/wiki_ls<N>.html` | Wikipedia "List of members of the Nth Lok Sabha": seat, member, and party. The first line holds the page revision id. |
| `raw/wiki_redirects.json` | Wikipedia link title to article title. |
| `results/speaker_terms.tsv` | One row for each (member, term) pair on the sansad.in lists. |
| `results/report.md` | The counts of the build. |
| `results/rejects.tsv` | The pairs that the matcher refused. |
| `results/last_term_disagreements.tsv` | The last terms where sansad.in and Wikipedia give different parties. It has an empty `review` column. |

### Hand-made files

All files are tab-separated and have a header row.

- `party_codes.tsv`: `wiki_party`, `code`, `note`. It maps a Wikipedia party name that sansad.in cannot map to a party code. An empty code means that the party is not known.
- `party_changes.tsv`: `term`, `mpsno`, `name`, `seat`, `from_party`, `to_party`, `date`, `date_source`, `kind`, `wiki_note`, `review`. Each change of party inside a term. It came once from the Wikipedia notes. Edit it by hand. Use a Wikipedia date only when you confirmed it.
- `party_events.tsv`: `term`, `mpsno`, `name`, `effective_from`, `party`, `constituency`, `kind`, `source`, `note`. The loader reads it. A row of kind `election` has no date and gives the party at the election where a source was wrong. Other rows are formal changes inside a term with a date: by-election, split, merger, or expulsion.
- `manual.tsv`: `term`, `mpsno`, `name`, `last_term`, `turns`, `words`, `why`, `party`, `constituency`, `source_url`, `note`. The (member, term) pairs that have no party after all rules. Fill `party` with a known party code and give a source link. The build refuses an unknown code.
- `non_member_parties.tsv`: `term`, `mpsno`, `name`, `party`, `note`. The party of a speaker who is not a Lok Sabha member in the term, for example a Rajya Sabha minister.
- `manual_states.tsv`: `term`, `mpsno`, `name`, `constituency`, `speakers_source`, `state`, `source_url`, `note`. The (member, term) pairs that get no state from `speaker_terms.tsv` or from sansad.in. Fill `state` by hand and give a source link. The loader reads this file last. A filled `state` replaces the state of every row of that pair. An empty `state` changes nothing, so the state stays empty. The loader stops if one pair has two rows.

## How a member is matched to a Wikipedia row

1. The matcher compares names only inside one term.
2. A pair is kept only when each side is the single best candidate of the other. A tie keeps nothing.
3. In the last term, sansad.in knows the seat. A pair in a different seat is never kept.
4. One Wikipedia article is one person. If an article matches two member codes, only the matches with a confirmed seat stay.
5. A member with one article in other terms takes the free row with that article.
6. In the last term, a member takes the only free row in the sansad.in seat. The two names must share one word that is not a common name word, such as Singh or Kumar.
7. The article fill runs again with the articles that the seat fill found.
8. A row in `manual.tsv` with a party replaces the result for that pair.

The column `method` records the rule: `name+seat`, `name`, `article`, `seat`, or `manual`.

## Rules for the data

- **The party follows the House record, with dates.** Each (member, term) has a first row from the first day of the term. A formal event in `party_events.tsv` adds a row from its date. A member who only works for another party keeps the party of the House record. A suspension changes nothing.
- **A speech takes the row that is true on the date of its debate.** The view `speaker_periods` gives each row the date on which the next row starts.
- **A change after the last sitting of a term affects no speech.**
- **The constituency is for matching and display only.** Do not join on it, group by it, or compare it across terms. The spellings differ and the seat boundaries changed.
- **A miss is acceptable. A wrong person is not.** A member with no match gets a row with no party and the source `sansad-term-list`.
- **A speaker with no Lok Sabha seat in the term keeps the last-term party.** The loader adds a row with the source `last-term-fallback` and no constituency, unless `non_member_parties.tsv` gives a party.

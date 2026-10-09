# Place tags for districts and constituencies

This folder holds place tags for the districts of India and for the 543 current Lok Sabha constituencies. The seed tag list has only 206 place tags. A district like Meerut or Kannauj had no tag. This folder fills that gap.

The linking step (`scripts/link_entities.py`) has an exact-match rule. When an entity name equals the name or an alias of exactly one tag, the name links to that tag without the decision model. When it equals two or more tags, the decision model decides. So every new name and alias in this folder can make automatic links. A wrong link is worse than no link. The rules below follow from this fact.

## The result

`results/place_tags.tsv` holds 933 new tags. It has the same columns as the seed file: `tag`, `type`, `subtype`, `domain`, `description`, `aliases`, `debate_count`. Every tag has the type `place`, the domain `-` (like the existing state tags), and `debate_count` 0.

| Subtype | Tags | Meaning |
|---|---|---|
| `district` | 398 | A district that is not a constituency of the same name in the same state. |
| `constituency` | 148 | A Lok Sabha constituency that is not a district of the same name in the same state. |
| `district_constituency` | 383 | One district and one constituency with the same name in the same state. They share ONE tag. |
| `former_constituency` | 4 | An old Assam constituency that no longer exists. See rule 10. |

The input has 788 district rows and 543 constituency rows. 13 places have no new tag, because an existing tag has their name or alias. The 13 places are listed in `results/review_pairs.tsv` (kind `existing_exact`). Examples are Chandigarh, Ranchi, Kargil, and Sikkim. Three of them (`Daman and Diu`, `Andaman and Nicobar Islands`, and `Puducherry`) lost their tag because the seed list got an alias for them. `Kutch` lost its tag for the same reason: the seed tag `Kachchh Region` is the same place, and it now has the aliases `Kutch` and `Kachchh`. See `results/alias_review.md`.

15 tags have the state in the name, for example `Hamirpur (Uttar Pradesh)`. 28 old district names are in use as aliases. 156 aliases exist in total. The other aliases are the bare name of a shared name, the ASCII spelling of a name with a diacritic (`Mahé` and `Mahe`), the other dash character of a name with a dash (`Janjgir-Champa` and `Janjgir–Champa`), the second spelling of a merged place (rule 8), and the 59 hand-checked aliases of `data/extra_aliases.tsv`.

The file `results/build_report.md` shows the counts for each state and the result of each self check.

## Sources

| List | Source used | URL | Download date |
|---|---|---|---|
| Districts | Wikipedia, "List of districts in India" (fallback) | https://en.wikipedia.org/wiki/List_of_districts_in_India | 2026-10-09 |
| Constituencies | Wikipedia, "List of constituencies of the Lok Sabha" (fallback) | https://en.wikipedia.org/wiki/List_of_constituencies_of_the_Lok_Sabha | 2026-10-09 |

Both files are the rendered page (`action=render`) in one HTML file each. They are in `data/raw/districts/` and `data/raw/constituencies/`. Nobody edited them.

Why a fallback:

- The Local Government Directory (lgdirectory.gov.in) shows a CAPTCHA on its download page. The work did not try to solve or bypass the CAPTCHA.
- The Election Commission site (eci.gov.in) redirects to a results application that builds its pages with scripts. The work found no static list of the 543 constituencies on it.

The Wikipedia districts page states 802 districts in its summary box. The overview table states 800. The state tables hold 788 rows. See "Known faults".

The hand-made file `data/renames.tsv` holds the district renames. Each row has a source URL. The column `checked` says `yes` when a Wikipedia summary was read in this work and confirmed the rename. It says `no` when the row comes from general knowledge and nobody checked it. Check the `no` rows before you trust their year.

## Rules

1. Each district and each constituency becomes a tag of type `place`.
2. A district and a constituency with the same name in the same state make ONE tag. The subtype is `district_constituency`. The description is "District and Lok Sabha constituency in STATE, India." The merge uses the name only. A constituency can cover parts of several districts. So the merge says "same name", not "same area".
3. A constituency suffix `(SC)` or `(ST)` is not in the name. The class is in `results/place_sources.tsv`, column `reserved`.
4. A name that two or more places in different states claim gets the state in brackets, for example `Aurangabad (Bihar)`. A claim is a current name or an old name from `renames.tsv`. Each such tag gets the bare name as an alias. The bare name then equals two or more tags. In `scripts/link_entities.py`, `Tags.exact` collects the ids of all tags for one `norm_name`, and `exact_tag` returns an id only when exactly one id exists. So the exact rule does not fire and the decision model decides.
5. A place whose name equals the name or an alias of an existing tag gets no new tag. The comparison uses `norm_name` from `scripts/link_entities.py`. The script imports it. An alias of a new tag that equals an existing name or alias is dropped, and a review row says so.
6. An old district name from `renames.tsv` is an alias of the tag with the new name. The Wikipedia lists still show some old names (for example Osmanabad). In that case the tag gets the new name and the old name is the alias.
7. The script adds no Hindi alias and no invented spelling. It adds only two systematic spelling forms: the name without diacritics, and the name with the other dash character. Every other alias comes from a hand-made file (rules 8 to 10).
8. A pair in `data/same_place.tsv` makes ONE tag. The columns are `name_a`, `name_b`, `state`, `keep`, and `note`. One name is a district and the other name is a constituency of the same place in the same state, with two spellings. The rule for `keep` is the district spelling. The other spelling is an alias, and the description says "The constituency is listed as X." The build stops with an error when a row names a missing place or two places of one kind. The file has 26 pairs. The first 8 pairs came from the spelling key: Kutch and Kachchh, Kanchipuram and Kancheepuram, Thoothukudi and Thoothukkudi, Viluppuram and Villupuram, Kushinagar and Kushi Nagar, Raebareli and Rae Bareli, Shravasti and Shrawasti, Chikkaballapur and Chikballapur. A person checked the other 18 pairs in `results/alias_review.md`. Each of them has one district and one constituency in one state. The pairs are Jehanabad and Jahanabad, Surguja and Sarguja, Mehsana and Mahesana, Hazaribag and Hazaribagh, Balangir and Bolangir, Kendujhar and Keonjhar, Kanyakumari and Kanniyakumari, Tiruvallur and Thiruvallur, Peddapalli and Peddapalle, Budaun and Badaun, Bagpat and Baghpat, Sri Ganganagar and Ganganagar, Alipurduar and Alipurduars, West Champaran and Paschim Champaran, East Champaran and Purvi Champaran, Ananthapuramu and Anantapur, YSR Kadapa and Kadapa, and Lakhimpur Kheri and Kheri. The alias of the last pair is `Kheri`. The bare name `Lakhimpur` is not an alias, because `Lakhimpur` is an Assam constituency. The hand-made alias `Ananthapur` now belongs to `Ananthapuramu` in `data/extra_aliases.tsv`.
9. A row in `data/extra_aliases.tsv` adds one alias to one new tag. The columns are `alias`, `tag`, `state`, `items`, `evidence`, and `reason`. A person must read example mentions before a row enters the file. The self checks reject an alias that equals the name or alias of any other tag.
10. Each seat of the old Assam constituency table needs one row in `data/old_seats.tsv`. The decision is `same` (the old name is already a name or alias), `alias` (the old name becomes an alias of the tag in `target`), `former` (the seat gets its own tag), or `ignore` (no change, the note says why). The build stops with an error for a seat without a row.

### The Maharashtra Aurangabad case

The Wikipedia district list names the district Aurangabad. The district has the official name Chhatrapati Sambhajinagar since 2023. The constituency list still says Aurangabad. The script handles this case in four steps:

1. The district gets the name `Chhatrapati Sambhajinagar`, with the alias `Aurangabad`.
2. The constituency `Aurangabad` in Maharashtra has the same name as the old district name. So it joins the district tag. The tag has the subtype `district_constituency`. The description ends with "The constituency is listed as Aurangabad."
3. The Bihar district and constituency `Aurangabad` make the tag `Aurangabad (Bihar)`, with the alias `Aurangabad`.
4. The bare name `Aurangabad` now equals two tags. The decision model decides. The review file shows this case as `shared_name` and as `rename`.

Ahmednagar (Ahilyanagar), Osmanabad (Dharashiv), and Gurgaon (Gurugram) work in the same way. A person must still check whether the old constituency and the renamed district describe the same area.

## The review file

`results/review_pairs.tsv` has one row for each possible duplicate or risk. The column `review` is empty. Fill it by hand. `results/review_pairs.md` shows the first 15 rows of each kind.

| Kind | Rows | Meaning |
|---|---|---|
| `existing_exact` | 13 | A source place equals an existing tag name or alias. No new tag. |
| `existing_near` | 1 | A source place has the spelling key of an existing tag, or the hand-made file `data/near_hints.tsv` links them. Review only. |
| `shared_name` | 14 | A bare name shared by new tags in different states. |
| `common_word` | 31 | A place name that is also an ordinary word. |
| `rename` | 28 | An alias from `renames.tsv`. |
| `new_near` | 0 | Two new tags of one state with the same spelling key. The pairs that this kind found are now merged (rule 8). |

The spelling key is `spelling_key` from `entity_lookup.py`. It also merges different places (`Gond` and `Gonda` have the same key). So no row is a merge. For `existing_near`, the script removes a last generic word such as `Region` before it makes the key.

The method for `common_word`:

1. `english_word`: the name in lower case is an all-lower-case entry of `/usr/share/dict/words`. A proper noun has a capital letter in that list. The list holds many rare words (`surat`, `thane`, `satara`). So this method gives many false alarms.
2. `hand_list`: the name is in `data/common_words.tsv`. A person made this list. It has 8 words.
3. `entity_name`: the name equals an entity name of another type in the speeches (`speech_items`, type is not `place`). `scripts/check_place_coverage.py` writes `results/db_entity_names.tsv` for this method.
4. A name that equals an existing tag of another type gets no new tag. It appears as `existing_exact`. The script does not repeat it as `common_word`.

The method cannot find a Hindi word that is not in these lists. A person read the 31 rows and the speeches. The result is the list `MODEL_ONLY` in `scripts/link_entities.py`. For a name on that list, the exact match rule does not apply, and the decision model decides, even when exactly one tag has the name. The list has 22 names. The comment in the code says why: these place names are also ordinary words. The reasons follow.

- `basti`, `mandi`, `daman`, `guna`, `banda`, `sagar`, `dhar`, `mau`, `pali`: Hindi words (a settlement, a market, subdue, a quality, a man or servant, the sea, a flow, and so on) or a common person name.
- `krishna`: a god and a very common person name. The name is also a river and a district.
- `sham`: Hindi evening, and a short form of the name Shyam.
- `mon`: an English abbreviation for Monday.
- `surat`, `gaya`, `kota`, `agar`, `anand`: Hindi words in common speech (a face or a situation, went, a quota, if, joy). Speeches in Hindi use them in every sentence.
- `dang` (Hindi for stunned), `samba` (the dance), `korea` (the country, and also a district in Chhattisgarh), `patan` (Hindi for a fall, and a town in Nepal), `panna` (Hindi for a page).

The system word list also flagged `Arrah`, `Bidar`, `Balaghat`, `Raver`, `Satara`, `Thane`, `Sikar`, `Erode`, `Solan`, and `Tonk`. These are not on `MODEL_ONLY`. Their English meaning is rare or does not appear in the entity names of the speeches. The names `Polavaram` and `Panipat` appear once as another entity type. They stay on the exact rule.

## How to rebuild

```bash
source .venv/bin/activate
python3 -I scripts/build_place_tags.py
```

The script reads `data/` and the seed file. It calls no model and writes nothing to the database. It writes the files in `results/`. The flag `-I` stops Python from loading code from the data folders. The script exits with an error when a self check fails. The self checks are:

- No two new tags have the same `norm_name`.
- No new name or alias equals an existing tag name or alias.
- No alias equals the name of another new tag.
- An alias that belongs to two or more new tags must be an intended shared bare name or a shared old name.
- The source has 543 constituency rows.
- No district name or constituency name appears twice in one state.
- Every alias of `data/extra_aliases.tsv` passes all the checks above. Every old Assam seat has a decision.

The coverage check reads the database with SELECT statements only. It needs the database settings in `.env`:

```bash
set -a && source .env && set +a
python3 scripts/check_place_coverage.py
python3 -I scripts/build_place_tags.py   # again, so that common_word rows can use db_entity_names.tsv
```

The coverage check also writes `results/db_unmatched_names.tsv`. It lists every place name that matches no tag, with the item count. The person who adds aliases reads this file.

The tests are in `tests/test_build_place_tags.py`. The frozen inputs are `tests/data/places_*_mini.*`.

## The coverage check

`results/coverage_check.md` has the result. Read it as a measure of coverage. It counts names that equal a tag. It does not count names that link to the RIGHT place. The denominators are the 8,796 distinct place names and the 73,027 place items in `speech_items` (type `place`, list `other`).

| Group | Names | Items | Before the alias work |
|---|---|---|---|
| Equals exactly one new tag | 880 | 21,639 | 822 names, 21,399 items |
| Equals two or more new tags | 8 | 485 | 8 names, 485 items |
| Equals an existing tag | 146 | 33,347 | 124 names, 31,743 items |
| Equals nothing | 7,762 | 17,556 | 7,842 names, 19,400 items |

Of the 880 names with exactly one new tag, 20 names (701 items) are on the `MODEL_ONLY` list. The exact rule skips them. The decision model decides.

Only 131 of the 271,957 items in `speech_items` have a judge result, and only 31 of the 73,027 place items are kept. The linking step reads only kept items. So the table counts all extracted place items, not the items that the linking step will see.

## Added aliases

The alias work has three sources. The file `results/alias_review.md` has the evidence, 20 sample aliases, the rejected candidates, and the proposals.

| Source | Aliases | Items | Where |
|---|---|---|---|
| `data/extra_aliases.tsv` | 59 | 466 | On new tags. Example: `Malda` is an alias of `Maldah`. |
| Seed list rows `manual review, 2026-10-09` | 20 on 10 tags | about 1,600 | `tags/seed_tags_v1/data/review.tsv`. Example: `Jammu and Kashmir`. |
| Old Assam seats (`data/old_seats.tsv`) | 1 | 1 | `Gauhati` is an alias of `Guwahati`. |

## Old Assam constituencies

The raw constituency page holds two tables for Assam. The second table has the 14 seats before the 2023 delimitation. The speeches of Lok Sabha 16 and 17 use these names. The file `data/old_seats.tsv` has one decision for each seat.

| Old seat | Decision | Reason |
|---|---|---|
| Karimganj, Silchar, Dhubri, Kokrajhar, Barpeta, Jorhat, Lakhimpur | `same` | A current tag or alias already has the name. `Karimganj` is the old name of the district Sribhumi. |
| Gauhati | `alias` of `Guwahati` | An older spelling of the same city and seat. |
| Mangaldoi | `former` | `Darrang-Udalguri` replaced it in 2023 and also covers Udalguri. |
| Tezpur | `former` | `Sonitpur` replaced it in 2023 and the boundaries changed. 10 items use the name, most of them for the town. |
| Kaliabor | `former` | `Kaziranga` replaced it in 2023 and the boundaries changed. |
| Autonomous District | `former`, tag name `Autonomous District (Assam)` | The seat is now `Diphu`, but nothing in this repository confirms the rename. The name is also an ordinary phrase, so the tag name has the state and no bare alias. |
| Nowgong | `ignore` | The old spelling of Nagaon. A town in Madhya Pradesh has the same name. |
| Dilbrugarh | `ignore` | A typing error of Dibrugarh in the source table. |

A former tag has the description "Former Lok Sabha constituency in Assam, India (until 2024)." The raw page has no table of the old Jammu and Kashmir seats (before the 2022 delimitation). So the work did not check them. For example, `Anantnag` is now `Anantnag–Rajouri`. The tag `Anantnag` exists as a district, so the old name works for the district.

## Known faults

- The source is Wikipedia, not the Local Government Directory and not the Election Commission. A Wikipedia page can have errors or lag behind the official data.
- The page states different district counts in different places. The overview table says Nagaland 17, West Bengal 27, and Delhi 13. The state tables list 16, 23, and 11. So the tags miss some districts. The script does not add a district that the source does not list. `results/build_report.md` lists the differences.
- The district page is current in 2026 and includes new districts. Districts that existed in 2014 and were merged later are not in the list. Speeches before the merge can use their names.
- The old Assam seats are handled in `data/old_seats.tsv`. The old Jammu and Kashmir seats are not handled, because the raw page has no table of them.
- The merge of a district and a constituency uses the name only.
- 17 of the 28 rows in `data/renames.tsv` have `checked` = `no`. This work did not check them against a source.
- The tags are not in the database. `scripts/load_tags.py` deletes seed tags that are not in the seed file. So loading these tags needs a decision on the source label and a loader change.
- The tags have no embedding. The vector search finds them only after `scripts/embed_tags.py` runs.
- Cities (Mumbai, Bengaluru, Kochi), rivers, and regions are not in scope. They are the largest gap in the coverage check.
- Spelling variants of names with fewer than 3 items stay unmatched. The alias work did not check them.
- Three pairs of `results/alias_review.md` stay as two tags, because each pair holds two different places. `Bangalore South` is a Bengaluru city seat, and `Bengaluru South` is the 2025 new name of the Ramanagara district. `Garhwal` is also a large region, and `Pauri Garhwal` is a district. `Medinipur` is a town and a seat, and `Paschim Medinipur` is a district. The other 18 pairs are merged (rule 8).
- The linking step has a name-only rule. Two places in different states can have the same name, and only one of them has a tag. The tag `Chitrakoot` (Uttar Pradesh) catches the town Chitrakoot in Madhya Pradesh. 12 of its 146 items have a debate title with Madhya Pradesh. The same risk exists for `Balrampur`.

## Done, next, and unknown

Done: the source files, the script, the 933 tags, the review file, the tests, the coverage check, the 26 merged pairs (18 merged and 3 rejected from the list of 21 likely pairs), the `MODEL_ONLY` list, the 59 extra aliases, the 20 seed aliases, and the old Assam seats.

Next: a person fills the `review` column and decides on the proposed aliases in `results/alias_review.md`. Then someone decides how to load the tags (source label, loader), embeds them, and runs the linking step in `--dry-run` mode to see the new exact links.

Unknown: how many exact links are correct. The coverage check does not measure this. It is also unknown which other ordinary words can cause a wrong link in real speeches. The `MODEL_ONLY` list comes from reading the 31 flagged rows and the single-word tag names once. It is not complete. It is also unknown whether `Autonomous District` is the old name of `Diphu`.

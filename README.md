# Torko

Torko lets a user search 64,921 Lok Sabha debates from 1999 to 2026 and find every speech by 2,072 identified members of parliament.

![Debate search](docs/images/dashboard-search.png)

## The problem

The official website [sansad.in](https://sansad.in/ls/debates/digitized) publishes each Lok Sabha debate as a separate web page. The archive starts with the 13th Lok Sabha, in 1999. This is a major improvement from erstwhile PDF-only versions of debates (available on [eparlib](https://elibrary.sansad.in/collections/b2770639-c57b-4ba3-a9f1-57761c60d195) site)

At first view, the data looks well structured and machine-readable. Each speaker has a unique identity number. Each debate lists the members who took part. A researcher could expect to list every intervention by one member.

A closer look shows four problems.

**1. The identity number appears only on a member's first turn in a debate.** Later turns carry only a printed name. The same person also appears under many spellings, for example `SHRI ADHIR RANJAN CHOWDHURY (BAHARAMPUR)`, `SHRI ADHIR RANJAN CHOWDHURY`, and `श्री अधीर रंजन चौधरी`.

**2. One number can name different ministers.** A minister who is not a Lok Sabha member gets a temporary number for one term. A later term gives the same number to a different person. For example, `10008` is Anbumani Ramadoss in LS14 (2004 to 2009) and Ravi Shankar Prasad in LS16 (2014 to 2019).

**3. The list of participants is incomplete.** There are numerous cases where interventions of a speaker are left untagged altogether. In this [2002 debate](https://sansad.in/ls/debates/view-debate?ls=13&session=11&dbslno=4930), Tarit Baran Topdar speaks 3 times. The list of participants does not include his name. So sansad.in does not link this debate to him. Torko finds all 3 turns and links them to him.

![Tarit Baran Topdar speaks, but the participant list omits him](docs/images/tarit-topdar-special-mention.png)

**4. Old Hindi text is unreadable.** Debates before about 2009 store Hindi in a pre-Unicode font inside the source HTML. The text shows as random Latin characters. See [this 2001 debate](https://sansad.in/ls/debates/view-debate?ls=13&session=7&dbslno=2890) for an example.

![Hindi text in the old font, as sansad.in shows it](docs/images/hindi-pre-unicode-example.png)

## What Torko does

- Search 26+ years (1999 - 2026) of debates by word or by phrase.
- Filter debates by party, by parliament term, by year, and by category.
- Open a member of parliament and read every speech from that member.
- Open the official source page for any speech, with one click.

## Terms used in this project

This table defines the terms that this project uses.

| Term                  | Meaning                                                                                                                                   | Example                                                          |
| --------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------- |
| **Lok Sabha**         | The lower house of India's parliament.                                                                                                    |                                                                  |
| **Term**              | One elected Lok Sabha, about 5 years long. Torko covers the 13th to the 18th term.                                                        | LS17 = June 2019 to February 2024                                |
| **Session**           | One sitting period inside a term. A term has about 15 sessions.                                                                           | LS18, Session 7                                                  |
| **Debate**            | One item of business on one day. sansad.in publishes each debate as a separate page. <br><br>There can be multiple debates on a given day | "Papers laid on the Table", 17 April 2026                        |
| **Speaker label**     | The name text printed above a block of speech on the sansad.in website.                                                                   | `SHRI ADHIR RANJAN CHOWDHURY (BAHARAMPUR)`                       |
| **Member**            | A specific person who sat in the Lok Sabha. <br><br>Torko gives each member one permanent identity across all terms.                      | Adhir Ranjan Chowdhury                                           |
| **Member ID**         | The number that sansad.in gives each member. The number stays the same across terms.                                                      | `97`                                                             |
| **Turn**              | One unbroken block of text under one speaker label. A debate is a list of turns. A turn is the smallest unit of a debate.                 | One reply between two interruptions counts as a turn.            |
| **Speech**            | One continuous contribution by one member. We stitch together a member's turns across short interruptions to create a speech.             | A 90-minute reply with 40 interruptions is 1 speech and 41 turns |
| **Interjection**      | A short turn from another member inside someone's speech. A remark of 25 words or fewer does not end the speech.                          | "Sir, that is not correct."                                      |
| **Presiding officer** | The person in the chair, such as the Speaker or the Deputy Speaker. sansad.in prints the office, not the name.                            | `MR. SPEAKER`                                                    |
| **Attributed turn**   | A turn that Torko links to one member successfully.                                                                                       |                                                                  |
| **Unattributed turn** | A turn that Torko cannot link to one member conclusively. Torko leaves the name blank. It does not guess.                                 |                                                                  |
| **Debate category**   | The type of business that sansad.in assigns to each debate. There are 76 categories.                                                      | `MATTERS UNDER RULE-377`                                         |
| **sansad.in keyword** | A subject keyword that sansad.in attaches to a whole debate. 70.5% of debates have one or more keywords.                                  | `Coastal Areas`                                                  |
| **Tag**               | A subject in Torko's own vocabulary. Torko gives tags to each speech, not to a whole debate.                                              | `Road Construction`                                              |
| **Old-font Hindi**    | Hindi text in debates before about 2009, stored in a pre-Unicode font. It looks like broken Latin letters until Torko decodes it.         | `gÉÉÒ` = श्री                                                    |

## Run it

Follow these steps to run Torko locally:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Copy the example environment file and set a database password.

```bash
cp .env.example .env
```

Start the database with this command.

```bash
docker compose up -d
```

### Load the data

The database starts empty. Run these five commands one time, in this order.

```bash
python3 scripts/load_roster.py
python3 -u scripts/import_debates.py
python3 -u scripts/populate_turns.py
python3 -u scripts/populate_speeches.py
python3 scripts/analyze_speeches.py > fixtures/analysis.json
```

The first script loads the member roster from the sansad.in API.
The second script downloads all 64,921 debates.
This step takes under one hour with the default 6 workers.
The third script reads the stored HTML and writes the speaking turns.
The fourth script groups the turns into speeches.
The fifth command rebuilds the data for the corpus statistics page.

Start the web server with this command.

```bash
source .venv/bin/activate && set -a && source .env && set +a && python3 server.py
```

Open the dashboard at this address: http://localhost:5050/dashboard.html

Torko also runs from the command line, on a single debate at a time.

```bash
python3 debate_fetch.py --loksabha 18 --session 3 --dbslno 1758
python3 debate_fetch_legacy.py --loksabha 13 --session 14 --dbslno 7793
```

Add the `--summary-only` flag to hide the per-turn previews.

## Screenshots

![Member profile](docs/images/speaker-profile.png)
This image shows the profile page for one member of parliament.

## How it works

1. The reader fetches each debate from the sansad.in API.
2. Torko stores the raw HTML of the debate before it reads any text.
3. The reader extracts each speaking turn and writes it to PostgreSQL.
4. A Flask API, a Python web framework, serves the stored data to the front-end.

Torko is built with Python, PostgreSQL, SQLAlchemy Core, Flask, and plain JavaScript. SQLAlchemy Core is a Python toolkit for writing SQL queries.

Raw HTML is stored in the DB before any text is parsed out of that HTML. Thus, a change to the parsing logic does not need new network requests. A full re-read of all 64,921 debates takes minutes to complete, without any dependency on sansad.in.

Two reader files turn HTML into speaking turns. `debate_fetch.py` reads the recent format, used from the 15th to the 18th Lok Sabha. `debate_fetch_legacy.py` reads the old format, used in the 13th and 14th Lok Sabha. Torko detects the correct reader on its own, for each debate.

## Two engineering problems

**Problem 1: the disguised Hindi font.** Old pages store Hindi text in a font that predates Unicode, the modern standard for text encoding. The stored bytes look like broken Latin characters, for example `gÉÉÒ`. A reader that ignores this stores meaningless text while it reports success. Torko builds a character map to convert the bytes into real Hindi text. Torko also builds a detector. The detector decides whether the conversion should run. The detector matters because one early version of the fix once converted correct Hindi text into damaged text.

The character map does not fix all of the text. In 1,413 turns of the 13th Lok Sabha, most Hindi words stayed unreadable. We repaired these turns with the help of an LLM and a manual review. The repairs also showed that 1,177 of these turns held the speech of more than one person, so we split them into one turn for each speaker. The repaired turns are in [`data/turn_text_repairs.tsv`](data/turn_text_repairs.tsv), and a rebuild applies them again.

**Problem 2: one identity across 26 years.** The same person must carry one identity across all 6 parliament terms Torko covers. The source gives a stable identity number only on a speaker's first turn in each debate. Later turns carry just a printed name. Torko carries the identity number forward to later turns by comparing the printed names. Torko records no name when two different people could match the same printed name. A gap is safer than a wrong name.

Torko links all three spellings of Adhir Ranjan Chowdhury's name from the earlier example to one person record. That single record holds 861 debates and 2,397 interventions. It holds 552,048 words in total. The record spans 5 parliament terms, from 1999 to 2024.

## The numbers covered in the project

| Metric                                            | Value                                                                             |
| ------------------------------------------------- | --------------------------------------------------------------------------------- |
| Debates                                           | 64,921                                                                            |
| Date range                                        | 20 October 1999 to 18 April 2026                                                  |
| Parliament terms                                  | 6 (the 13th to the 18th Lok Sabha)                                                |
| Speaking turns                                    | 526,701                                                                           |
| Stitched speeches                                 | 173,225                                                                           |
| Members in the loaded roster                      | 2,178                                                                             |
| Members with at least one attributed turn         | 2,076                                                                             |
| Total words                                       | 76,543,432                                                                        |
| Words linked to a named person                    | 61,737,420 (81% of total words)                                                   |
| Turns with no identified speaker (chair excluded) | 106,168                                                                           |
| Speeches of 100 words or more with a named person | 99,975                                                                            |
| Debate categories                                 | 76                                                                                |
| sansad.in keywords                                | 6,976 distinct keywords, on 70.5% of debates                                      |
| Average speech length                             | 415 words                                                                         |
| Longest single speech                             | 103,632 words                                                                     |
| Debates per term                                  | LS13: 7,616. LS14: 11,027. LS15: 11,216. LS16: 15,831. LS17: 13,272. LS18: 5,959. |


## Known limits

1. Torko finds no speaker name for 106,168 turns. The dashboard marks these turns as unattributed.
2. The party shown for a speech is the member's party on the date of the debate. It comes from the Wikipedia list of members of each term, from sansad.in, and from a manual review. A change of party inside a term shows from its date only when it is a formal event, such as a by-election, a recognised split, or an expulsion. Changes that no source records are not shown. See [`data/party_history`](data/party_history/README.md).
3. Torko does not read about 13.6% of the source text. The loss is 32.5% in the 13th Lok Sabha and about 3% in recent terms. Charts over time will therefore show too little activity in the early years.

   <details>
   <summary>Why?</summary>

   Each reader collects text only from paragraph tags (`<p>`). Many source pages have broken HTML. A `<p>` tag opens but never closes. The HTML library then closes that tag early. The rest of the speech sits outside any paragraph, under a `<font>` tag or directly under `<body>`. The readers do not look there, so that text is lost.

   </details>

## Next steps

**1. Tags for each speech.** sansad.in attaches keywords to a whole debate, not to a single speech. One large debate can carry 59 keywords, and most of them do not apply to any single speech in it. Some subjects also have no keyword at all. For example, members discuss jallikattu in 26 debates, but only 1 of them has a keyword for it. Torko will give each speech its own tags and a one-line summary. Torko will record which model produced each tag, and on which date. With these tags, a user can rank members by subject and see how a subject changes over time.

The plan has these steps. Each step has a folder under `tags/` with its own README.

1. **Seed list. Done.** 4,473 tags come from the sansad.in keywords that appear in 2 or more debates. Two LLM steps typed the keywords and merged the ones that mean the same thing. A second list adds 933 place tags: one for each district and each current Lok Sabha constituency. Scripts rebuild both lists from stored files and call no model. See [`tags/seed_tags_v1`](tags/seed_tags_v1/README.md) and [`tags/places`](tags/places/README.md).
2. **Tag embeddings. Done.** PostgreSQL stores each tag with an embedding. An embedding is a list of numbers that represents the meaning of a text. See [`tags/embedding_v1`](tags/embedding_v1/README.md).
3. **Extraction. Done for LS 13 to 18.** For each speech of 99 or more words with a known member, an LLM writes a one-sentence summary and lists at most 8 topics and 8 named entities. See [`tags/extraction_v1`](tags/extraction_v1/README.md).
4. **More candidates. Done for LS 13 to 18.** The extraction misses some subjects. An entity dictionary finds known entity names in the speech text, and the tags nearest to the summary in meaning become candidates too. See [`tags/entity_dictionary`](tags/entity_dictionary/README.md) and [`tags/summary_tags`](tags/summary_tags/README.md).
5. **Relevance check. Done for LS 13 to 18.** A decision model checks each candidate against the speech and keeps only the real subjects. A decision model cannot write text. It picks from fixed answers and gives a probability for each one. See [`tags/judging`](tags/judging/README.md).
6. **Links. Done for LS 13 to 18.** Each kept entity links to one tag, or to none. A name with exactly one tag of the same spelling links with no model call. A link needs a high probability, because a wrong tag is worse than no tag. See [`tags/linking`](tags/linking/README.md).
7. **New tags.** Torko groups the entities with no tag by meaning. A group that appears in 10 or more speeches, in 3 or more debates, becomes a candidate tag. It stays unverified until a person reviews it. Then the unmatched entities are matched again against the larger list.
8. **Subjects under tags. Built for LS 16, 17, and 18.** A broad tag such as `Arrears` holds many specific subjects, for example sugarcane farmers' arrears and wage arrears. Torko keeps these specific subjects visible, so a link to a broad tag loses no detail. Names that mean almost the same thing form small groups by the distance of their embeddings. An LLM then decides which close groups are one subject, because distance alone cannot tell this: "Sugarcane pricing" sits next to "Sugarcane arrears". On 243 test pairs that two other models labelled blind, the LLM made no wrong join and found 74% of the true joins. No person checked these labels yet. Each subject gets a short label. A decision model chooses its parent tag: the tag that means the same thing as the subject, or the tag that the subject is one part of. A tag that is only one part of the subject is not its parent. 4,387 of the 11,080 subjects have a parent. The others have no clear parent, because a wrong parent is worse than none. A search for "arrears" returns the tag with all its subjects. A search for "farmers arrears" returns the one subject. See [`tags/subject_groups`](tags/subject_groups/README.md).
9. **Merges of near-duplicate tags. Done.** Some tags of the seed list mean the same thing, for example `Rail Budget` and `Railway Budget`. They split the vote of the link step, so the entity gets no tag. A manual review accepted 185 merges. A merge must not make a tag more general than what the speeches say. The merged tags keep their rows, marked as merged, and their names become aliases of the kept tag. The link step then ran again on the names whose vote was split. See [`tags/near_duplicates`](tags/near_duplicates/README.md).

**2. Semantic search.** Today, search matches exact words. The next step after tags is search by meaning. A query such as "water scarcity in rural districts" will also find speeches that use other words for the same idea. Each speech of 100 words or more will be converted into an embedding. There are 97,043 such speeches. PostgreSQL will store the embeddings with the `pgvector` extension. One query will combine meaning, exact words, and filters such as party and year. Each result will link to the official source.

**Ideas we may explore after these steps.** We may pick the following based on what the first two steps show.

- **Connections between topics and members.** Torko already records which member spoke in which debate, and who interrupted whom. Speech-level tags will add a new layer to these links. Then Torko can answer questions such as "Which members raised both coastal erosion and cyclone relief?"

- **Questions in plain language.** A user types a question. A small LLM converts it into filters for a known query and shows those filters to the user. The database, not the LLM, produces every result.

- **Topics over time.** Charts that show how often parliament discussed a topic in each session, and which members led the discussion.

- **Better source data.** Read the text that Torko misses today, find the changes of party in earlier terms that no source records, and record who chaired each sitting.

## Tests

The tests run with no network access. A few tests read the local database, so load `.env` first. The full run takes a few seconds.

```bash
set -a && source .env && set +a && python3 -m pytest
```

## License

Released under the MIT License.

-- Terms, members, parties, chair roles, and the two tables that fix the member
-- of a turn.

-- lok_sabhas: one row for each Lok Sabha term. The rows are fixed, so this file
-- inserts them. Torko covers terms 13 to 18.
CREATE TABLE IF NOT EXISTS lok_sabhas (
    number      INT  PRIMARY KEY,
    start_date  DATE,
    end_date    DATE                    -- NULL for the current term
);

INSERT INTO lok_sabhas (number, start_date, end_date) VALUES
    (13, '1999-10-20', '2004-02-06'),
    (14, '2004-06-02', '2009-05-18'),
    (15, '2009-06-01', '2014-05-18'),
    (16, '2014-06-04', '2019-05-24'),
    (17, '2019-06-17', '2024-06-05'),
    (18, '2024-06-24', NULL)
ON CONFLICT (number) DO NOTHING;


-- persons: one row for each real member. This is Torko's own permanent identity
-- for a member, the same in every term.
--
-- sansad_id is the member number (mpsno) of the sansad.in member directory. It
-- is unique, but it is not the primary key. The debate transcripts use a
-- different numbering (mpCode). See mpcode_aliases below.
CREATE TABLE IF NOT EXISTS persons (
    id          SERIAL PRIMARY KEY,
    name        TEXT NOT NULL,          -- the name to show
    sansad_id   INT  UNIQUE             -- mpsno, from the sansad.in member API
);


-- parties: one row for each political party. speakers.party_id points here.
--
-- code  the short code, for example INC or SHSUBT. sansad.in gives most codes.
--       The file data/party_history/party_codes.tsv gives the rest.
-- name  the full name. scripts/load_roster.py and scripts/load_party_history.py
--       write it.
--
-- TODO: links between parties, for example 'renamed from' (TRS to BRS) and
-- 'split from' (Shiv Sena to Shiv Sena UBT).
CREATE TABLE IF NOT EXISTS parties (
    id    SERIAL PRIMARY KEY,
    code  TEXT NOT NULL UNIQUE,
    name  TEXT NOT NULL
);


-- states: one row for each state or union territory of a Lok Sabha seat, with one fixed name.
-- The loader maps each source spelling to this name with data/party_history/state_names.tsv.
-- A renamed state keeps one row (Orissa is Odisha). A state with a new area is a new row
-- (Ladakh is not Jammu and Kashmir, and the merged Dadra and Nagar Haveli and Daman and Diu
-- is not either of its two parts).
-- tag_id is the place tag of the state, or NULL. It is NULL when no place tag of subtype state or
-- union_territory has this name, or when more than one has it. It has no foreign key, because
-- the tags table is created in a later file.
CREATE TABLE IF NOT EXISTS states (
    id      SERIAL PRIMARY KEY,
    name    TEXT NOT NULL UNIQUE,
    tag_id  INT
);

-- speakers: the party and the seat of a member in one term, from one date.
--
-- A member has one row for each term in which the member sat. A member whose
-- party changed inside a term has more than one row for that term.
--
-- effective_from  the first day on which the row is true. The first row of a
--                 (member, term) starts on the first day of the term
--                 (lok_sabhas.start_date). A later row starts on the date of a
--                 formal event in data/party_history/party_events.tsv: a
--                 by-election, a split or a merger that the House recognised,
--                 or an expulsion. A member who only works for another party
--                 keeps the party of the House record. A suspension changes
--                 nothing.
-- source          where the row comes from:
--   sansad-last-term    the sansad.in member record. sansad.in gives the party
--                       and the seat for the member's last term only.
--   wikipedia           the Wikipedia list of members of that term, matched to
--                       the member.
--   sansad-term-list    sansad.in says that the member sat in the term, but no
--                       Wikipedia row matched. Party and seat are NULL.
--   manual              a manual review gave the row.
--   last-term-fallback  the member has turns in a term in which the member was
--                       not a Lok Sabha member, mostly a minister from the Rajya
--                       Sabha. The row copies the party of the member's last
--                       Lok Sabha term. The seat is NULL.
--   event               a later row of the term, from party_events.tsv. It
--                       copies the seat of the first row of the term.
-- match_method    how a wikipedia row was matched: name+seat, name, article,
--                 seat, or manual.
--
-- For a speech on date D, the party is the party of the member's row in the
-- debate's term with the latest effective_from on or before D. The view
-- speaker_periods below gives each row its end date.
--
-- WARNING: constituency is a text copy of the source spelling. Use it only to
-- match a member to a term and to show it to a reader. Do not join on it, group
-- by it, or compare it across terms. Spellings differ across sources, and seat
-- boundaries changed with the delimitation orders of 1976 and 2008.
-- TODO: a constituency table with one row per seat and delimitation order.
CREATE TABLE IF NOT EXISTS speakers (
    id              SERIAL PRIMARY KEY,
    person_id       INT  NOT NULL REFERENCES persons(id),
    lok_sabha_term  INT  NOT NULL REFERENCES lok_sabhas(number),
    name            TEXT,                  -- the name as recorded in that term
    constituency    TEXT,
    state_id        INT  REFERENCES states(id),  -- the state of the seat, NULL if not known
    source          TEXT CHECK (source IN ('sansad-last-term', 'wikipedia', 'sansad-term-list', 'manual',
                                           'last-term-fallback', 'event')),
    match_method    TEXT CHECK (match_method IN ('name+seat', 'name', 'article', 'seat', 'manual')),
    party_id        INT  REFERENCES parties(id),
    effective_from  DATE NOT NULL,
    CONSTRAINT speakers_term_person_from_key UNIQUE (lok_sabha_term, person_id, effective_from)
);

COMMENT ON COLUMN speakers.constituency IS
    'Source spelling, for matching and display only. Do not use in business logic.';

CREATE INDEX IF NOT EXISTS speakers_person_term_idx ON speakers (person_id, lok_sabha_term, effective_from);

-- speaker_periods: each speakers row with the day on which the next row of the
-- same (member, term) starts. effective_to is NULL for the last row. A debate on
-- date D uses the row with effective_from <= D and
-- (effective_to IS NULL or D < effective_to).
CREATE OR REPLACE VIEW speaker_periods AS
SELECT s.*,
       lead(s.effective_from) OVER (PARTITION BY s.person_id, s.lok_sabha_term
                                    ORDER BY s.effective_from) AS effective_to
FROM speakers s;


-- speaker_roles: the speaker labels that name an office or a crowd, not a
-- person.
--   presiding  the Chair, printed by office ("MR. SPEAKER:", "अध्यक्ष महोदय:").
--   crowd      an interjection by many members ("SEVERAL HON. MEMBERS:",
--              "अनेक माननीय सदस्य:").
--
-- These rows are not in persons, and they have no sansad_id. "MR. SPEAKER" in
-- terms 13 to 18 is at least five different people. One row in persons would
-- say that they are one person, and every count for that person would be wrong.
--
-- resolvable says if a label can ever name one person. A presiding officer is a
-- real person: a future table of who held the office on which dates can name
-- them. A crowd label can never name one person.
--
-- The rows are offices, not spellings. The corpus prints 143 spellings of these
-- labels. The parser finds the office word in the label, so the spellings need
-- no rows. The Hindi forms are the same offices: अध्यक्ष = Speaker,
-- उपाध्यक्ष = Deputy Speaker, सभापति = Chairman.
CREATE TABLE IF NOT EXISTS speaker_roles (
    id           SMALLSERIAL PRIMARY KEY,
    code         TEXT NOT NULL UNIQUE,     -- the slug that the parser writes. Never renumber.
    kind         TEXT NOT NULL CHECK (kind IN ('presiding', 'crowd')),
    display_name TEXT NOT NULL,
    resolvable   BOOLEAN NOT NULL,
    notes        TEXT
);

INSERT INTO speaker_roles (code, kind, display_name, resolvable, notes) VALUES
    ('speaker', 'presiding', 'Speaker', TRUE,
     'अध्यक्ष / अध्यक्ष महोदय / MR./MADAM/HON. SPEAKER. One person per term; the page does not name them, which is why they must come from a tenure table.'),
    ('deputy_speaker', 'presiding', 'Deputy Speaker', TRUE,
     'उपाध्यक्ष / MR. DEPUTY-SPEAKER. Matched before `speaker` -- the string contains it.'),
    ('chairman', 'presiding', 'Chairman', TRUE,
     'सभापति / MR./MADAM CHAIRMAN / HON. CHAIRPERSON. Unlike the Speaker this office rotates among a panel of MPs during a sitting, which is why the page sometimes prints the name alongside it -- see the 140 role+person labels.'),
    ('deputy_chairman', 'presiding', 'Deputy Chairman (Rajya Sabha)', TRUE,
     'DEPUTY-CHAIRMAN (RAJYA SABHA). 58 occurrences, LS13 and LS15: the OTHER House''s presiding officer appearing in a Lok Sabha transcript. Its own office, not a spelling of `chairman` -- a different human entirely. Matched before `chairman`, which its string contains. NOTE: the "(RAJYA SABHA)" suffix is a CHAMBER, not a person, so any future rule that reads a name out of a role label''s parentheses must exclude this form or it will invent a member called "Rajya Sabha".'),
    ('members_crowd', 'crowd', 'Several/Some Hon. Members', FALSE,
     'SEVERAL/SOME/MANY HON. MEMBERS, अनेक/कई/कुछ माननीय सदस्य. Deliberately ONE row: several-vs-some carries no attribution information, so splitting them would invent a distinction the data does not make.')
ON CONFLICT (code) DO NOTHING;


-- mpcode_aliases: a debate member code (mpCode) that names one person.
--
-- The transcripts identify a speaker by mpCode. The roster identifies a person
-- by mpsno (persons.sansad_id). These are two different numberings. They often
-- agree, but they also collide: mpCode 572 is H. D. Deve Gowda in a debate, but
-- mpsno 572 is Taherali Abdullabhai, a member of the 1st Lok Sabha.
--
-- A row exists only when the printed name labels of that code all point to
-- exactly one person in the roster. A code whose labels name two people gets no
-- row. Codes 10000 and above are left out: the source reuses them for
-- different ministers (10008 is Ravi Shankar Prasad and also Anbumani Ramadoss).
-- scripts/populate_mpcode_aliases.py fills this table.
CREATE TABLE IF NOT EXISTS mpcode_aliases (
    mp_code        TEXT PRIMARY KEY,               -- the debate code (turns.mp_code)
    person_id      INT  NOT NULL REFERENCES persons(id),
    evidence_turns INT  NOT NULL,                  -- turns whose name label supports the row
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS mpcode_aliases_person_idx ON mpcode_aliases (person_id);


-- label_aliases: a speaker label that names one member, for turns that the
-- parser could not link to a member.
--
-- A label is the speaker name as the transcript prints it before a turn, for
-- example "डॉ. सत्यपाल सिंह ( बागपत )". Some labels stay unlinked, mostly labels
-- in Hindi or Urdu script. An LLM chose one member from the roster for each
-- such label, and a person reviewed a sample of the answers.
--
-- The key is the term plus the exact label, after the removal of extra spaces.
-- A row for one term never applies in another term.
--
-- scripts/populate_turns.py uses a row only when the parser found no member and
-- no chair role for the turn. Such a turn has name_source 'label-alias'. The
-- source of the rows is the tracked file data/label_aliases.tsv, and
-- scripts/load_label_aliases.py loads it.
CREATE TABLE IF NOT EXISTS label_aliases (
    loksabha      SMALLINT NOT NULL REFERENCES lok_sabhas(number),
    speaker_label TEXT     NOT NULL,   -- the label after normalize_label()
    person_id     INT      NOT NULL REFERENCES persons(id),
    basis         TEXT     NOT NULL,   -- name_and_constituency, name, constituency, office
    source        TEXT     NOT NULL,   -- how the row was made and checked
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (loksabha, speaker_label)
);

CREATE INDEX IF NOT EXISTS label_aliases_person_idx ON label_aliases (person_id);

-- The parser output: speeches and turns.
--
-- A turn is one unbroken block of text under one speaker label. A speech is a
-- span of one member's turns across short interruptions. speech_stitch.py
-- holds the rule. scripts/populate_turns.py and scripts/populate_speeches.py
-- fill these tables.

-- speeches: one row for each speech.
--
-- A speech is a span over turns. It owns only the turns of its member. An
-- interruption inside the span stays its own turn, and the speech counts it but
-- does not take its words. So a speech never holds the words of another person.
--
--   person_id set   a known member owns the speech.
--   person_id NULL  a real speech by a person that the parser could not name.
--                   Two such turns are never joined, because nothing proves that
--                   they are the same person.
--
-- Chair and crowd turns never own a speech. They only bridge interruptions.
CREATE TABLE IF NOT EXISTS speeches (
    id                 BIGSERIAL PRIMARY KEY,
    debate_id          BIGINT  NOT NULL REFERENCES debates(id),
    person_id          INT     REFERENCES persons(id),  -- NULL = a person with no name

    seq_start          INTEGER NOT NULL,  -- seq of the first owned turn
    seq_end            INTEGER NOT NULL,  -- seq of the last owned turn
    turn_count         INTEGER NOT NULL,  -- the owner's turns only
    interruption_count INTEGER NOT NULL,  -- the other turns inside the span

    word_count         INTEGER NOT NULL,  -- over the owned turns only
    char_count         INTEGER NOT NULL,

    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT speeches_debate_seq UNIQUE (debate_id, seq_start)
);

CREATE INDEX IF NOT EXISTS speeches_debate_idx ON speeches (debate_id);
CREATE INDEX IF NOT EXISTS speeches_person_idx ON speeches (person_id);


-- turns: one row for each speaking turn that the parser found.
--
-- person_id and role_id are both nullable. In practice at most one is set:
--   person_id set  the turn belongs to a known member.
--   role_id set    the label names an office or a crowd (speaker_roles), never
--                  a row of persons.
--   neither set    the parser could not name the speaker. The turn stays, with
--                  no name.
-- role_kind copies speaker_roles.kind, so the frontend can show a chair turn
-- with no join. speaker_roles is a fixed table of five rows, so the copy is safe.
--
-- name_source says how the parser named the speaker: anchor, name-exact,
-- name-partial, name-translit, name-db, anchor-reuse, label-alias, presiding,
-- crowd, or unresolved. It lets an audit of wrong names work with no new parse.
--
-- text_source says where the text comes from:
--   NULL           the parser wrote the text from debates.raw_html (almost every turn).
--   'repair-llm'   an LLM repaired garbled old-font Hindi in the text.
--   'repair-dict'  a program of dictionary and rules repaired garbled old-font Hindi.
-- scripts/apply_turn_text_repairs.py sets the repair values from
-- data/turn_text_repairs.tsv. scripts/populate_turns.py writes new rows with
-- NULL, so a rebuild must run the repair script again.
--
-- speech_id links the turn to its speech. It is NULL for chair turns, crowd
-- turns, and short interjections that no speech owns.
CREATE TABLE IF NOT EXISTS turns (
    id            BIGSERIAL PRIMARY KEY,
    debate_id     BIGINT  NOT NULL REFERENCES debates(id),
    seq           INTEGER NOT NULL,   -- the order in the debate, from 0

    speaker_label TEXT,               -- the printed label, kept also when the turn has a member
    mp_code       TEXT,               -- the mpCode that the parser saw, if any

    person_id     INT      REFERENCES persons(id),
    role_id       SMALLINT REFERENCES speaker_roles(id),
    role_kind     TEXT CHECK (role_kind IN ('presiding', 'crowd')),
    name_source   TEXT,

    text          TEXT NOT NULL,
    word_count    INTEGER NOT NULL,
    char_count    INTEGER NOT NULL,
    text_source   TEXT CHECK (text_source IN ('repair-llm', 'repair-dict')),

    speech_id     BIGINT REFERENCES speeches(id),

    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT turns_debate_seq UNIQUE (debate_id, seq)
);

CREATE INDEX IF NOT EXISTS turns_debate_idx ON turns (debate_id);
CREATE INDEX IF NOT EXISTS turns_person_idx ON turns (person_id);
CREATE INDEX IF NOT EXISTS turns_speech_idx ON turns (speech_id);

-- Full-text search over the text of every turn (the dashboard filter
-- "Transcript contains"). Without this index the search scans the whole table.
-- The config is 'simple', not 'english': the text mixes English and Hindi, and
-- no stemmer fits both. 'simple' only lowercases and splits words. The query
-- must use the same config:
--     to_tsvector('simple', text) @@ plainto_tsquery('simple', :q)
-- A few tokens over 2,047 characters are skipped with a NOTICE. That is harmless.
CREATE INDEX IF NOT EXISTS turns_text_fts_idx
    ON turns USING GIN (to_tsvector('simple', text));

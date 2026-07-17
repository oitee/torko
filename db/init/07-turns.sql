-- turns: one row per parser-detected speaking turn (NOT stitched speeches --
-- see internal_docs, speechification is a later todo). A turn is a parse
-- artifact: one person's remarks split by interruption may be many turns.
--
-- person_id and role_id are both nullable and mutually exclusive in practice:
--   - person_id set   -> resolved to a specific human (persons.id).
--   - role_id set     -> a non-person label (presiding officer or crowd),
--                        FK'd straight to speaker_roles -- never a row in
--                        persons (see 06-speaker-roles.sql for why).
--   - neither set      -> genuinely unresolved. Never guessed; never dropped.
-- role_kind duplicates speaker_roles.kind at insert time so the FE can render
-- "presiding officer" differently without a join -- safe to denormalize
-- because speaker_roles is a static, five-row table.
CREATE TABLE IF NOT EXISTS turns (
    id            BIGSERIAL PRIMARY KEY,
    debate_id     BIGINT  NOT NULL REFERENCES debates(id),
    seq           INTEGER NOT NULL,   -- order within the debate, 0-based

    speaker_label TEXT,               -- raw printed label, kept even when resolved
    mp_code       TEXT,               -- raw mpCode the parser saw, if any (debug/audit)

    person_id     INT     REFERENCES persons(id),
    role_id       SMALLINT REFERENCES speaker_roles(id),
    role_kind     TEXT CHECK (role_kind IN ('presiding', 'crowd')),

    name_source   TEXT,               -- anchor/name-exact/name-partial/name-translit/
                                       -- name-db/anchor-reuse/presiding/crowd/unresolved
                                       -- kept so a future misattribution audit (cf. 026)
                                       -- doesn't need a full reparse.

    text          TEXT NOT NULL,
    word_count    INTEGER NOT NULL,
    char_count    INTEGER NOT NULL,

    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT turns_debate_seq UNIQUE (debate_id, seq)
);

CREATE INDEX IF NOT EXISTS turns_debate_idx ON turns (debate_id);
CREATE INDEX IF NOT EXISTS turns_person_idx ON turns (person_id);

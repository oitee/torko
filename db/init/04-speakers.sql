-- speakers: one row per (person, Lok Sabha term). Holds party / constituency
-- as they were in that term.
--
-- For the initial roster load we create ONE speaker per person, attached to that
-- person's own last term. The sansad member API reports details for the latest term
-- only for that MP; hence storing Per-term
-- Later stage: Will backfill memebrs for earlier term from third-party sources
CREATE TABLE IF NOT EXISTS speakers (
    id              SERIAL PRIMARY KEY,
    person_id       INT  NOT NULL REFERENCES persons(id),
    lok_sabha_term  INT  NOT NULL REFERENCES lok_sabhas(number),
    name            TEXT,                 -- name as recorded that term
    party           TEXT,
    constituency    TEXT,
    UNIQUE (lok_sabha_term, person_id)
);

-- TODO (indexes, deferred per request): fuzzy speaker matching needs a trigram
-- index for `name % query` / similarity():
--   CREATE INDEX speakers_name_trgm ON speakers USING GIN (name gin_trgm_ops);

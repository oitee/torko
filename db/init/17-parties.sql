-- parties: one row for each political party. speakers.party_id points here.
--
-- Before this file, speakers.party held the party code as free text. Now each code exists
-- once, in this table, and a filter by party compares ids.
--
-- code  the short code, for example INC or SHSUBT. sansad.in gives most codes. A hand-made
--       list (data/party_history/party_codes.tsv) gives the rest.
-- name  the full name. scripts/load_roster.py and scripts/load_party_history.py write it.
--
-- TODO: links between parties, for example 'renamed from' (TRS to BRS) and 'split from'
-- (Shiv Sena to Shiv Sena UBT), when the party of a member gets dates inside a term.
CREATE TABLE IF NOT EXISTS parties (
    id    SERIAL PRIMARY KEY,
    code  TEXT NOT NULL UNIQUE,
    name  TEXT NOT NULL
);

ALTER TABLE speakers ADD COLUMN IF NOT EXISTS party_id INT REFERENCES parties(id);

-- Move the old text codes into the table. 'Not Available' is not a party: it becomes NULL.
-- The name starts as the code. The loaders write the full names.
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_name = 'speakers' AND column_name = 'party') THEN
        INSERT INTO parties (code, name)
            SELECT DISTINCT party, party FROM speakers
            WHERE party IS NOT NULL AND party <> 'Not Available'
            ON CONFLICT (code) DO NOTHING;
        UPDATE speakers sp SET party_id = pa.id FROM parties pa WHERE pa.code = sp.party;
        ALTER TABLE speakers DROP COLUMN party;
    END IF;
END $$;

-- A new source of rows:
--   last-term-fallback  the member has turns in a term in which the member was not a Lok Sabha
--                       member, mostly a minister from the Rajya Sabha. The row copies the
--                       party of the member's last Lok Sabha term. The constituency is NULL.
--                       TODO: a real party for speakers who are not Lok Sabha members.
ALTER TABLE speakers DROP CONSTRAINT IF EXISTS speakers_source_check;
ALTER TABLE speakers ADD CONSTRAINT speakers_source_check
    CHECK (source IN ('sansad-last-term', 'wikipedia', 'sansad-term-list', 'manual', 'last-term-fallback'));
ALTER TABLE speakers DROP CONSTRAINT IF EXISTS speakers_match_method_check;
ALTER TABLE speakers ADD CONSTRAINT speakers_match_method_check
    CHECK (match_method IN ('name+seat', 'name', 'article', 'seat', 'manual'));

-- speakers: more than one row for a (member, term) when the member's party changed inside
-- the term. Each row holds the date from which it is true.
--
-- effective_from  the first day on which the row is true. The first row of a (member, term)
--                 starts on the first day of the term (lok_sabhas.start_date). A later row
--                 starts on the date of a formal event in data/party_history/party_events.tsv:
--                 a by-election, a split or a merger that the House recognised, or an
--                 expulsion. A member who only works for another party keeps the party of the
--                 House record. A suspension changes nothing.
--
-- For a speech on date D, the party is the party of the member's row in the debate's term with
-- the latest effective_from on or before D.
--
-- A row of source 'event' copies the constituency of the first row of the term.
ALTER TABLE speakers ADD COLUMN IF NOT EXISTS effective_from DATE;

UPDATE speakers sp SET effective_from = ls.start_date
FROM lok_sabhas ls
WHERE ls.number = sp.lok_sabha_term AND sp.effective_from IS NULL;

ALTER TABLE speakers ALTER COLUMN effective_from SET NOT NULL;

ALTER TABLE speakers DROP CONSTRAINT IF EXISTS speakers_lok_sabha_term_person_id_key;
ALTER TABLE speakers DROP CONSTRAINT IF EXISTS speakers_term_person_from_key;
ALTER TABLE speakers ADD CONSTRAINT speakers_term_person_from_key
    UNIQUE (lok_sabha_term, person_id, effective_from);

CREATE INDEX IF NOT EXISTS speakers_person_term_idx ON speakers (person_id, lok_sabha_term, effective_from);

ALTER TABLE speakers DROP CONSTRAINT IF EXISTS speakers_source_check;
ALTER TABLE speakers ADD CONSTRAINT speakers_source_check
    CHECK (source IN ('sansad-last-term', 'wikipedia', 'sansad-term-list', 'manual',
                      'last-term-fallback', 'event'));

-- speaker_periods: each speakers row with the day on which the next row of the same
-- (member, term) starts. effective_to is NULL for the last row. A debate on date D uses the row
-- with effective_from <= D and (effective_to IS NULL or D < effective_to).
CREATE OR REPLACE VIEW speaker_periods AS
SELECT s.*,
       lead(s.effective_from) OVER (PARTITION BY s.person_id, s.lok_sabha_term
                                    ORDER BY s.effective_from) AS effective_to
FROM speakers s;

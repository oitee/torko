-- speakers: one row for each (member, Lok Sabha term), not only for the last term.
--
-- Before this file, each member had one row, for their last term, with the party and the
-- constituency from sansad.in. sansad.in gives these for the last term only. Now
-- scripts/load_party_history.py adds a row for every other term in which the member sat.
--
-- source says where the row came from:
--   sansad-last-term  sansad.in member record. Party and constituency are for the last term.
--   wikipedia         the Wikipedia list of members of that term, matched to the member.
--   sansad-term-list  sansad.in says that the member sat in the term, but no Wikipedia row
--                     matched. Party and constituency are NULL: not known.
-- match_method says how a wikipedia row was matched: name+seat, name, article, or seat.
--
-- WARNING: speakers.constituency is a text copy of the source spelling. It exists only to help
-- match a member to a term, and to show to a reader. Do not use it in business logic: do not
-- join on it, group by it, or compare it across terms. Spellings differ across sources, and seat
-- boundaries changed with the delimitation orders of 1976 and 2008.
-- TODO: a constituency table with one row per seat and delimitation order, if a feature needs it.
ALTER TABLE speakers ADD COLUMN IF NOT EXISTS source TEXT
    CHECK (source IN ('sansad-last-term', 'wikipedia', 'sansad-term-list'));
ALTER TABLE speakers ADD COLUMN IF NOT EXISTS match_method TEXT
    CHECK (match_method IN ('name+seat', 'name', 'article', 'seat'));

UPDATE speakers SET source = 'sansad-last-term' WHERE source IS NULL;

COMMENT ON COLUMN speakers.constituency IS
    'Source spelling, for matching and display only. Do not use in business logic.';

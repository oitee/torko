-- Full-text keyword search over transcript bodies.
--
-- The dashboard's "Transcript contains" filter matches whole words in the text
-- of every turn (dashboard_db.list_debates, text_query param). Without an index
-- that is a sequential scan of the 587 MB turns table -- ~11.7s per query, and
-- the COUNT doubles it. This GIN index over the tokenised text drops the same
-- query to ~11ms.
--
-- Config is 'simple', not 'english': the corpus is polyglot (English + disguised
-- pre-Unicode Hindi in the legacy era) and no stemmer fits both. 'simple' just
-- lowercases and splits on non-word chars -- exactly the whole-word keyword
-- match the FE promises, no stemming surprises. The query side MUST use the same
-- config: to_tsvector('simple', text) @@ plainto_tsquery('simple', :q).
--
-- Applied by hand, like 06-speaker-roles.sql and 07-turns.sql (this DB predates
-- an auto-migration runner). Size: ~148 MB. A handful of tokens over 2047 chars
-- (base64 blobs pasted into a transcript) are skipped with a NOTICE -- harmless.
CREATE INDEX IF NOT EXISTS turns_text_fts_idx
    ON turns USING GIN (to_tsvector('simple', text));

-- Stage 4 judges candidates from more than one source. Every candidate of a
-- speech is a row of speech_items, so one judge, one keep rule, and one query
-- serve every source.
--
-- source:
--   llm          the extraction model listed the item (all rows before this change)
--   dictionary   the entity dictionary found a known entity name in the speech
--                text, and the extraction did not list it (list = 'other')
--   summary_tag  one of the tags nearest to the summary vector of the speech
--                (list = 'topic'). It is already a tag, so tag_id holds it and
--                stage 5 does not link it.
-- evidence: why the row exists. A dictionary row holds the number of matches
-- and its rank under the cap. A summary tag holds its cosine distance and rank.
-- The positions of added rows continue after the positions of the llm rows of
-- the same list.
ALTER TABLE speech_items
    ADD COLUMN IF NOT EXISTS source    TEXT NOT NULL DEFAULT 'llm'
        CHECK (source IN ('llm', 'dictionary', 'summary_tag')),
    ADD COLUMN IF NOT EXISTS tag_id    INTEGER REFERENCES tags(id),
    ADD COLUMN IF NOT EXISTS evidence  JSONB;

ALTER TABLE speech_items DROP CONSTRAINT IF EXISTS speech_items_summary_tag_has_tag;
ALTER TABLE speech_items ADD CONSTRAINT speech_items_summary_tag_has_tag
    CHECK ((source = 'summary_tag') = (tag_id IS NOT NULL));

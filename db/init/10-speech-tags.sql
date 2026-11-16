-- speech_tags_mv: the tags of each speech, stored. One row for each (speech, tag).
-- The rules: the item is kept. The tag comes from the item itself, or from its entity name when the name is linked.
-- A merged tag resolves to its kept tag. When two items give one tag, the row keeps the source in this order:
-- llm, dictionary, other.
--
-- The view does not update itself. Run scripts/refresh_speech_tags.py after each change to speech_items,
-- entity_names, or tags. scripts/build_tag_related.py runs it first.
-- The unique index lets REFRESH MATERIALIZED VIEW CONCURRENTLY run while the pages read the old rows.

CREATE MATERIALIZED VIEW IF NOT EXISTS speech_tags_mv AS
SELECT DISTINCT ON (si.speech_id, COALESCE(km.id, kt.id))
       si.speech_id, COALESCE(km.id, kt.id) AS tag_id, si.source
FROM speech_items si
LEFT JOIN entity_names en ON en.id = si.entity_name_id AND en.link_status = 'linked'
LEFT JOIN tags kt ON kt.id = COALESCE(si.tag_id, en.tag_id)
LEFT JOIN tags km ON km.id = kt.merged_into
WHERE si.kept AND kt.id IS NOT NULL
ORDER BY si.speech_id, COALESCE(km.id, kt.id),
         CASE si.source WHEN 'llm' THEN 0 WHEN 'dictionary' THEN 1 ELSE 2 END;

CREATE UNIQUE INDEX IF NOT EXISTS speech_tags_mv_speech_tag_key ON speech_tags_mv (speech_id, tag_id);
CREATE INDEX IF NOT EXISTS speech_tags_mv_tag_idx ON speech_tags_mv (tag_id);

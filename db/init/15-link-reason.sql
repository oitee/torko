-- Stage 5: the reason for a link.
--
-- link_reason says why the row holds its link:
--   exact_match  the full name has the same norm_name as exactly one tag name
--                or alias. No decision model call happened, and link_p is NULL.
--   model        the decision model decided.
-- A row from before this column has linked_by set and no link_reason.
-- The backfill below gives these rows the reason 'model', because the model
-- decided every one of them.
ALTER TABLE entity_names ADD COLUMN IF NOT EXISTS link_reason TEXT
    CHECK (link_reason IN ('exact_match', 'model'));

UPDATE entity_names SET link_reason = 'model' WHERE link_reason IS NULL AND linked_by IS NOT NULL;

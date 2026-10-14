-- turns.text_source: where the text of a turn comes from.
--
--   NULL          the parser wrote the text from debates.raw_html. This is true for almost every turn.
--   'repair-llm'  an LLM repaired garbled old-font Hindi in the text.
--   'repair-dict' a dictionary-and-rules program repaired garbled old-font Hindi in the text.
--
-- scripts/apply_turn_text_repairs.py sets the two repair values from data/turn_text_repairs.tsv.
-- scripts/populate_turns.py writes new turn rows with NULL, so a rebuild must run the repair
-- script again.
ALTER TABLE turns ADD COLUMN IF NOT EXISTS text_source TEXT;

ALTER TABLE turns DROP CONSTRAINT IF EXISTS turns_text_source_check;
ALTER TABLE turns ADD CONSTRAINT turns_text_source_check
    CHECK (text_source IN ('repair-llm', 'repair-dict'));

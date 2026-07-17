-- speeches: one row per stitched intervention. A speech is what a person
-- actually did; a `turns` row is only the parser's fragment of it. See
-- speech_stitch.py for the rule and the invariant that makes it safe.
--
-- A speech is a SPAN over turns, never a text-merge across speakers. It owns
-- only its owner's turns; interruptions inside the span stay their own turns
-- and are counted, not absorbed. So a speech can never carry another human's
-- words -- there is no attribution decision in stitching, only segmentation.
--
--   person_id set  -> a resolved human (persons.id) owns this speech.
--   person_id NULL -> a substantive turn we could not resolve: a real speech by
--                     an unknown human. Never stitched across (cannot prove two
--                     unresolved turns are the same person).
--
-- Presiding-officer and crowd turns NEVER own a speech (procedural, ~33% of all
-- turns); they only bridge interruptions. So speeches cover the analytical
-- population -- who said something -- not the whole turn stream.
CREATE TABLE IF NOT EXISTS speeches (
    id                 BIGSERIAL PRIMARY KEY,
    debate_id          BIGINT  NOT NULL REFERENCES debates(id),
    person_id          INT     REFERENCES persons(id),  -- NULL = unresolved human

    seq_start          INTEGER NOT NULL,  -- seq of the first owned turn
    seq_end            INTEGER NOT NULL,  -- seq of the last owned turn
    turn_count         INTEGER NOT NULL,  -- owner's turns only
    interruption_count INTEGER NOT NULL,  -- bridge turns inside the span

    word_count         INTEGER NOT NULL,  -- sum over owned turns only
    char_count         INTEGER NOT NULL,

    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT speeches_debate_seq UNIQUE (debate_id, seq_start)
);

CREATE INDEX IF NOT EXISTS speeches_debate_idx ON speeches (debate_id);
CREATE INDEX IF NOT EXISTS speeches_person_idx ON speeches (person_id);

-- Back-link every turn to the speech it belongs to (NULL for bridge/orphan
-- turns: presiding, crowd, and heckles that never joined a speech).
ALTER TABLE turns ADD COLUMN IF NOT EXISTS speech_id BIGINT REFERENCES speeches(id);
CREATE INDEX IF NOT EXISTS turns_speech_idx ON turns (speech_id);

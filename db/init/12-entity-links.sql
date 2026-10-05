-- Stages 4 and 5 of the tag pipeline.
--
-- Stage 4 (scripts/judge_items.py) asks the decision model which items of a
-- speech are real subjects of the speech. It fills the judge_* columns of
-- speech_items. Each item keeps its probabilities, so a new threshold needs
-- no new call: `kept` is computed again from the stored values.
--
-- Stage 5 (scripts/link_entities.py) links each distinct entity name to one
-- tag, or to no tag. One decision serves every speech that holds the name.

-- entity_names: one row per distinct (norm_name, type).
-- norm_name is the name in lower case, with single spaces, without outer
-- punctuation. name is the most frequent spelling among the kept items.
-- link_status:
--   pending  no decision yet for the current version and tag set
--   linked   tag_id holds the tag, link_p its probability
--   none     no tag fits, or the model was not sure enough
-- A link is never written into tags.aliases. tags.aliases is part of the text
-- that each tag vector reads, so a new alias would move the search space.
-- tag_set_version is the largest tags.id at decision time. When new tags
-- arrive, a 'none' with an older version becomes eligible again.
CREATE TABLE IF NOT EXISTS entity_names (
    id               BIGSERIAL PRIMARY KEY,
    norm_name        TEXT     NOT NULL,
    type             TEXT     NOT NULL,
    name             TEXT     NOT NULL,
    n_speeches       INTEGER  NOT NULL DEFAULT 0,  -- distinct speeches with a kept item of this name
    embedding_query  vector(1536),                  -- gemini-embedding-001, RETRIEVAL_QUERY, of `name`
    link_status      TEXT     NOT NULL DEFAULT 'pending' CHECK (link_status IN ('pending', 'linked', 'none')),
    tag_id           INTEGER  REFERENCES tags(id),
    link_p           REAL,                          -- probability of the top option
    candidates       JSONB,                         -- the options, their source, and their probabilities
    link_raw         JSONB,                         -- the model answer before the checks
    link_warnings    TEXT[]   NOT NULL DEFAULT '{}',
    linked_by        TEXT,                          -- model and question version
    linked_at        TIMESTAMPTZ,
    tag_set_version  INTEGER,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (norm_name, type)
);

-- Stage 4 columns (questions version q2).
-- Topics: judge_level_p holds P(level 0), P(level 1), P(level 2), P(level 3)
-- of the centrality rubric.
-- Named items: judge_role_p holds P(absent), P(aside), P(point).
-- judge_refers_p is the probability that the words of the speech refer to the
-- item's name without a guess. judge_type_p holds the probability of each type.
-- judge_type is the model's type when its probability is at least 0.7, else
-- NULL. Later stages use judge_type when it is set.
-- judge_state says what the model read: 'speech' (the speech text) or
-- 'summary' (the summary and the mentions, when the speech is too long).
ALTER TABLE speech_items
    ADD COLUMN IF NOT EXISTS judge_level_p   REAL[],
    ADD COLUMN IF NOT EXISTS judge_role_p    REAL[],
    ADD COLUMN IF NOT EXISTS judge_refers_p  REAL,
    ADD COLUMN IF NOT EXISTS judge_type_p    JSONB,
    ADD COLUMN IF NOT EXISTS judge_type      TEXT,
    ADD COLUMN IF NOT EXISTS kept            BOOLEAN,
    ADD COLUMN IF NOT EXISTS judge_state     TEXT CHECK (judge_state IN ('speech', 'summary')),
    ADD COLUMN IF NOT EXISTS judge_raw       JSONB,
    ADD COLUMN IF NOT EXISTS judge_warnings  TEXT[] NOT NULL DEFAULT '{}',
    ADD COLUMN IF NOT EXISTS judged_by       TEXT,
    ADD COLUMN IF NOT EXISTS judged_at       TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS entity_name_id  BIGINT REFERENCES entity_names(id);

CREATE INDEX IF NOT EXISTS speech_items_entity_name_idx ON speech_items (entity_name_id);

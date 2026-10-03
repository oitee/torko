-- tags: the tag vocabulary for speeches. One row per tag.
--
-- The seed rows come from tags/seed_tags_v1/results/seed_tags_v1.tsv
-- (scripts/load_tags.py). A later step can add tags that the pipeline makes
-- from speech entities. `source` says where a tag came from. `status` says
-- whether a human checked it:
--   reviewed    a manual review checked the list that holds this tag (the seed rows)
--   unverified  the pipeline made this tag, and no human checked it
--   rejected    a manual review refused this tag. The row stays, so that the
--               pipeline does not make the same tag again.
CREATE TABLE IF NOT EXISTS tags (
    id           SERIAL PRIMARY KEY,
    tag          TEXT    NOT NULL UNIQUE,
    type         TEXT    NOT NULL,
    subtype      TEXT,                       -- places only, else NULL
    domain       TEXT,                       -- NULL when the file says '-'
    description  TEXT    NOT NULL,
    aliases      TEXT[]  NOT NULL DEFAULT '{}',
    debate_count INTEGER NOT NULL DEFAULT 0, -- keyword-to-debate links, not debates
    source       TEXT    NOT NULL,           -- 'seed_v1', later 'promoted'
    status       TEXT    NOT NULL CHECK (status IN ('reviewed', 'unverified', 'rejected')),
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- tag_embeddings: one vector per tag, model, and task type.
--
-- A vector from one model or task type cannot be compared with a vector from
-- another. So every search must filter on `model` and `task_type`. Two task
-- types can live side by side for a comparison.
--
-- input_hash is the md5 of input_text. When the text of a tag changes, the
-- hash changes, and scripts/embed_tags.py embeds the tag again.
--
-- No vector index: a full scan of a few thousand rows takes milliseconds.
CREATE TABLE IF NOT EXISTS tag_embeddings (
    tag_id      INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    model       TEXT    NOT NULL,
    task_type   TEXT    NOT NULL,
    dims        INTEGER NOT NULL,
    input_text  TEXT    NOT NULL,
    input_hash  TEXT    NOT NULL,
    embedding   vector(1536) NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tag_id, model, task_type)
);

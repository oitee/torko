-- The tag list and the tag vectors.

-- tags: one row for each tag, a subject in Torko's own list.
--
-- scripts/load_tags.py loads the rows from the tag lists (SOURCES in that
-- script). Each list deletes and loads only the rows of its own source.
-- source says where a tag came from, for example 'seed_v1' or 'places_v1'.
-- status says whether a person checked it:
--   reviewed    a manual review checked the list that holds this tag
--   unverified  the pipeline made this tag, and no person checked it
--   rejected    a manual review refused this tag. The row stays, so that the
--               pipeline does not make the same tag again.
CREATE TABLE IF NOT EXISTS tags (
    id           SERIAL PRIMARY KEY,
    tag          TEXT    NOT NULL UNIQUE,
    type         TEXT    NOT NULL,
    subtype      TEXT,                       -- places only, else NULL
    domain       TEXT,                       -- NULL when the list says '-'
    description  TEXT    NOT NULL,
    aliases      TEXT[]  NOT NULL DEFAULT '{}',
    debate_count INTEGER NOT NULL DEFAULT 0, -- keyword-to-debate links, not debates
    source       TEXT    NOT NULL,
    status       TEXT    NOT NULL CHECK (status IN ('reviewed', 'unverified', 'rejected')),
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);


-- tag_embeddings: one vector for each tag, model, and task type.
--
-- A vector of one model or task type cannot be compared with a vector of
-- another. So every search must filter on model and task_type.
--
-- input_hash is the md5 of input_text. When the text of a tag changes, the hash
-- changes, and scripts/embed_tags.py embeds the tag again.
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

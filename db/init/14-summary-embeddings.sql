-- speech_summary_embeddings: one vector for the summary of one speech.
--
-- A summary is the short text that the extraction step writes for a speech
-- (speech_extractions.summary). The embedding model turns the summary into a
-- list of numbers. pgvector measures the cosine distance between this list and
-- the tag vectors in tag_embeddings. The nearest tags are the summary tags.
--
-- The vector uses the task type RETRIEVAL_QUERY, so that it matches the tag
-- vectors with the task type RETRIEVAL_DOCUMENT. The vector has length 1.
--
-- extraction_id is the primary key. When a new extraction replaces an old one,
-- the old extraction row goes, and ON DELETE CASCADE drops the old vector.
-- input_hash is the md5 of the summary. scripts/embed_summaries.py embeds a
-- summary again only when this hash changes.
--
-- Summaries of the model 'rule-stub' are fixed texts. They get no vector.
--
-- No vector index: the search compares one vector with a few thousand tag
-- vectors, and that scan takes milliseconds.
--
-- Applied by hand on an existing volume (the init folder runs only on a fresh
-- volume).
CREATE TABLE IF NOT EXISTS speech_summary_embeddings (
    extraction_id BIGINT  PRIMARY KEY REFERENCES speech_extractions(id) ON DELETE CASCADE,
    speech_id     BIGINT  NOT NULL REFERENCES speeches(id),
    model         TEXT    NOT NULL,
    task_type     TEXT    NOT NULL,
    dims          INTEGER NOT NULL,
    input_hash    TEXT    NOT NULL,
    embedding     vector(1536) NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS speech_summary_embeddings_speech_idx ON speech_summary_embeddings (speech_id);

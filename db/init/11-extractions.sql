-- Stage 3 of the tag pipeline:
-- what LLM found in each speech. scripts/extract_entities.py writes these.
--
-- models: one row per model name. The name rule-stub is a fixed answer with
-- no model call (a procedural speech, or a speech with no text).
CREATE TABLE IF NOT EXISTS models (
    id    SMALLINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name  TEXT NOT NULL UNIQUE
);

-- speech_extractions: at most one row per speech. The unique key makes the
-- script idempotent: a speech that already has a row is never sent again,
-- whatever model made the row. model_id names the model that made the row.
-- It is metadata for review and audit only. The name rule-stub means a fixed
-- answer with no model call.
-- prompt_version names the prompt file that made the row
-- (v1 = tags/extraction_v1/prompts/extract_v1.md). A prompt file is never
-- edited after a row uses it, so a row made with an older version is "stale".
CREATE TABLE IF NOT EXISTS speech_extractions (
    id          BIGSERIAL PRIMARY KEY,
    speech_id   BIGINT  NOT NULL REFERENCES speeches(id),
    model_id    SMALLINT NOT NULL REFERENCES models(id),
    prompt_version TEXT NOT NULL,           -- v1, v2: the prompt file version
    language    TEXT,                       -- en, hi, mixed (model answer)
    summary     TEXT    NOT NULL,
    warnings    TEXT[]  NOT NULL DEFAULT '{}',
    raw         JSONB,                      -- the model answer before the checks
    tokens      JSONB   NOT NULL DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (speech_id)
);

CREATE INDEX IF NOT EXISTS speech_extractions_model_idx ON speech_extractions (model_id);

-- speech_items: one row per topic or other entity in one extraction.
-- Later stages add their own columns (stage 4: the decision-model relevance check,
-- stage 5: the link to entity_names). model_salience is the 1-5
-- salience that the extraction model gave. It is stored for comparison only.
-- No decision uses it.
CREATE TABLE IF NOT EXISTS speech_items (
    id               BIGSERIAL PRIMARY KEY,
    extraction_id    BIGINT   NOT NULL REFERENCES speech_extractions(id) ON DELETE CASCADE,
    speech_id        BIGINT   NOT NULL REFERENCES speeches(id),
    list             TEXT     NOT NULL CHECK (list IN ('topic', 'other')),
    position         SMALLINT NOT NULL,     -- 1 = first in the model's list
    name             TEXT     NOT NULL,
    type             TEXT     NOT NULL,
    model_salience   SMALLINT,
    mention          TEXT     NOT NULL,
    mention_found    BOOLEAN  NOT NULL,     -- the mention is in the speech text
    UNIQUE (extraction_id, list, position)
);

CREATE INDEX IF NOT EXISTS speech_items_speech_idx ON speech_items (speech_id);

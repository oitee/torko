-- Arguments: the points that a speech makes for or against a bill.
-- argument_extract.py writes the rows. The input is one pair of a speech and a bill whose stance is 'for' or 'against'.
--
-- argument_extractions: one row for each pair. It holds the raw answer of the model.
-- input_sha256 is the hash of the input text, so a changed input becomes visible.
-- speech_arguments: one row for each point of the answer.
-- side is 'for' or 'against': the side of the point, which can differ from the stance of the speech.
-- quote_found is false when the quote is not in the speech text. Such a point is not shown.
-- bill_argument_id is the group of the point (bill_arguments). It is NULL when quote_found is false.

CREATE TABLE IF NOT EXISTS argument_extractions (
    id             BIGSERIAL PRIMARY KEY,
    speech_id      BIGINT   NOT NULL REFERENCES speeches(id) ON DELETE CASCADE,
    bill_id        INT      NOT NULL REFERENCES bills(id),
    model_id       SMALLINT NOT NULL REFERENCES models(id),
    prompt_version TEXT     NOT NULL,
    input_sha256   CHAR(64) NOT NULL,
    raw            JSONB    NOT NULL,
    warnings       TEXT[]   NOT NULL DEFAULT '{}',
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT argument_extractions_pair UNIQUE (speech_id, bill_id)
);

-- bill_arguments: one row for each group of points of one bill on one side. argument_group.py writes it.
-- label is one neutral phrase for the reason that the points share. model_id is NULL for a list with one
-- point, which needs no model call. input_sha256 is the hash of the list that the model read.
CREATE TABLE IF NOT EXISTS bill_arguments (
    id             BIGSERIAL PRIMARY KEY,
    bill_id        INT      NOT NULL REFERENCES bills(id),
    side           TEXT     NOT NULL CHECK (side IN ('for', 'against')),
    position       SMALLINT NOT NULL,
    label          TEXT     NOT NULL,
    model_id       SMALLINT REFERENCES models(id),
    prompt_version TEXT     NOT NULL,
    input_sha256   CHAR(64) NOT NULL,
    CONSTRAINT bill_arguments_position UNIQUE (bill_id, side, position)
);

CREATE INDEX IF NOT EXISTS bill_arguments_bill_idx ON bill_arguments (bill_id, side);

CREATE TABLE IF NOT EXISTS speech_arguments (
    id            BIGSERIAL PRIMARY KEY,
    extraction_id BIGINT   NOT NULL REFERENCES argument_extractions(id) ON DELETE CASCADE,
    speech_id     BIGINT   NOT NULL REFERENCES speeches(id) ON DELETE CASCADE,
    bill_id       INT      NOT NULL REFERENCES bills(id),
    position      SMALLINT NOT NULL,
    side          TEXT     NOT NULL CHECK (side IN ('for', 'against')),
    point         TEXT     NOT NULL,
    quote         TEXT     NOT NULL,
    quote_found   BOOLEAN  NOT NULL,
    bill_argument_id BIGINT  REFERENCES bill_arguments(id) ON DELETE SET NULL,
    CONSTRAINT speech_arguments_position UNIQUE (extraction_id, position)
);

CREATE INDEX IF NOT EXISTS speech_arguments_bill_idx ON speech_arguments (bill_id);

-- argument_vectors: one vector for each point (speech_arguments.point), for the order of the points before
-- the grouping. input_md5 is the md5 of the point text, so a changed point gets a new vector.
CREATE TABLE IF NOT EXISTS argument_vectors (
    argument_id BIGINT PRIMARY KEY REFERENCES speech_arguments(id) ON DELETE CASCADE,
    model       TEXT   NOT NULL,
    input_md5   CHAR(32) NOT NULL,
    vector      vector(1536) NOT NULL
);

-- Stances: the position of each speech on each kept bill of its debate.
-- scripts/judge_stances.py writes the rows. One row for each pair of a speech and a bill.
--
-- bill_id is the kept bill after the merge of spellings (COALESCE(bills.merged_into, bills.id)).
-- The debate is also stored by its natural key (loksabha, session, dbslno), because a rebuild of the
-- speeches can give new speech ids.
-- stance_p holds the probabilities of for, against, mixed, unclear, in that order.
-- reasons_p holds none, one, two, three or more. on_bill_p holds none, a small part, about half, most, all.
-- stance is the option with the highest probability, or 'unclear' when that probability is below the limit.
-- state_source is 'speech', or 'summary' when the speech was too long and its summary was sent in its place.
-- The stance of a member on a bill is a query over this table, not a stored column.

CREATE TABLE IF NOT EXISTS speech_stances (
    id               BIGSERIAL PRIMARY KEY,
    speech_id        BIGINT   NOT NULL REFERENCES speeches(id) ON DELETE CASCADE,
    bill_id          INT      NOT NULL REFERENCES bills(id),
    loksabha         SMALLINT NOT NULL,
    session          SMALLINT NOT NULL,
    dbslno           INTEGER  NOT NULL,
    question_version TEXT     NOT NULL,
    model            TEXT     NOT NULL,
    state_source     TEXT     NOT NULL CHECK (state_source IN ('speech', 'summary')),
    stance_p         REAL[]   NOT NULL,
    stance           TEXT     NOT NULL CHECK (stance IN ('for', 'against', 'mixed', 'unclear')),
    reasons_p        REAL[]   NOT NULL,
    on_bill_p        REAL[]   NOT NULL,
    tokens           INT      NOT NULL DEFAULT 0,
    judged_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT speech_stances_pair UNIQUE (speech_id, bill_id)
);

CREATE INDEX IF NOT EXISTS speech_stances_bill_idx ON speech_stances (bill_id);

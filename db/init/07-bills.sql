-- Bills: the bill or bills that the House considered in each government-bill
-- debate. bill_extract.py writes the rows of all three tables.
--
-- A debate is named by its natural key (loksabha, session, dbslno), not by
-- debates.id, because a rebuild of the debates gives new ids.

-- bills: one row for each bill.
-- bill_key is the name in lower case with only letters and digits, then '-',
-- then the year. Two bills with a different year never share a key.
-- amendment_ordinal is the number of a Constitution amendment bill, as words in
-- lower case, for example 'one hundred and thirty-first'.
-- summary is the summary of the bill. The merge step writes it: it copies the
-- summary of a bill with one summary, and asks a model to join two or more.
-- summary_model_id is the model that joined the summaries. It is NULL when the
-- step copied one summary.
-- act_name and act_number stay empty until an outside list of bills fills them.
-- merged_into points to the bill row that the merge step folded this row into.
CREATE TABLE IF NOT EXISTS bills (
    id                SERIAL   PRIMARY KEY,
    name              TEXT     NOT NULL,
    year              SMALLINT NOT NULL,
    bill_key          TEXT     NOT NULL UNIQUE,
    amendment_ordinal TEXT,
    summary           TEXT,
    summary_model_id  SMALLINT REFERENCES models(id),
    act_name          TEXT,
    act_number        TEXT,
    merged_into       INT      REFERENCES bills(id),
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);


-- bill_extractions: at most one row for each debate. It holds the model answer
-- before the checks (raw), and the hash of the input text that the model read.
-- When the input of a debate changes, its hash no longer matches.
-- warnings lists what the checks found, for example a name not in the text.
CREATE TABLE IF NOT EXISTS bill_extractions (
    id             BIGSERIAL PRIMARY KEY,
    loksabha       SMALLINT NOT NULL,
    session        SMALLINT NOT NULL,
    dbslno         INTEGER  NOT NULL,
    model_id       SMALLINT NOT NULL REFERENCES models(id),
    prompt_version TEXT     NOT NULL,
    input_sha256   CHAR(64) NOT NULL,
    raw            JSONB    NOT NULL,
    warnings       TEXT[]   NOT NULL DEFAULT '{}',
    tokens         JSONB    NOT NULL DEFAULT '{}',
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT bill_extractions_debate UNIQUE (loksabha, session, dbslno)
);


-- debate_bills: one row for each bill name in the answer of one debate.
-- printed is the name as the text prints it. quote is the sentence of the
-- input that holds the name.
-- extracted_role is the answer of the extraction model: 'moved' (the House
-- considers, passes, or introduces the bill in this debate) or 'mentioned'
-- (a speaker only names it). Only a 'moved' row keeps a summary.
-- checks_failed lists the script checks that failed: name, year, ordinal,
-- quote, role. A row with a failed check has no bill_id and is not kept.
-- name_found is true when the printed name is in the input text.
-- judge_role_p holds the probabilities of the decision model for moved,
-- mentioned, unsure. It is NULL until that step runs. judged_by names the
-- model and the question version, for example 'jev-1.13.0 b1'.
-- kept is the current decision: the checks passed and the role is moved. Later the decision
-- model can change it. A kept row has a bill_id.
CREATE TABLE IF NOT EXISTS debate_bills (
    id                BIGSERIAL PRIMARY KEY,
    extraction_id     BIGINT   NOT NULL REFERENCES bill_extractions(id) ON DELETE CASCADE,
    loksabha          SMALLINT NOT NULL,
    session           SMALLINT NOT NULL,
    dbslno            INTEGER  NOT NULL,
    position          SMALLINT NOT NULL,
    bill_id           INT      REFERENCES bills(id),
    printed           TEXT     NOT NULL,
    quote             TEXT     NOT NULL,
    extracted_role    TEXT,
    summary           TEXT,
    checks_failed     TEXT[]   NOT NULL DEFAULT '{}',
    name_found        BOOLEAN  NOT NULL,
    judge_role_p      REAL[],
    judged_by         TEXT,
    kept              BOOLEAN  NOT NULL,
    CONSTRAINT debate_bills_position UNIQUE (loksabha, session, dbslno, position)
);

CREATE INDEX IF NOT EXISTS debate_bills_bill_idx ON debate_bills (bill_id);

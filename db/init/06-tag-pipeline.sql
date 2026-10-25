-- The tag pipeline after the tag list: extractions (stage 3), candidates and
-- their check (stage 4), and the links of names to tags (stage 5).

-- models: one row for each model name. The name 'rule-stub' is a fixed answer
-- with no model call (a procedural speech, or a speech with no text).
CREATE TABLE IF NOT EXISTS models (
    id    SMALLINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name  TEXT NOT NULL UNIQUE
);


-- speech_extractions: stage 3. At most one row for each speech: what an LLM
-- found in the speech. scripts/extract_entities.py writes the rows.
--
-- The unique key makes the script idempotent: a speech with a row is never sent
-- again, whatever model made the row. model_id is metadata for review only.
-- prompt_version names the prompt file that made the row (v1 is
-- tags/extraction_v1/prompts/extract_v1.md). A prompt file is never edited
-- after a row uses it, so a row of an older version is "stale".
CREATE TABLE IF NOT EXISTS speech_extractions (
    id             BIGSERIAL PRIMARY KEY,
    speech_id      BIGINT   NOT NULL REFERENCES speeches(id),
    model_id       SMALLINT NOT NULL REFERENCES models(id),
    prompt_version TEXT     NOT NULL,
    language       TEXT,                     -- en, hi, or mixed (the model's answer)
    summary        TEXT     NOT NULL,
    warnings       TEXT[]   NOT NULL DEFAULT '{}',
    raw            JSONB,                    -- the model answer before the checks
    tokens         JSONB    NOT NULL DEFAULT '{}',
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (speech_id)
);

CREATE INDEX IF NOT EXISTS speech_extractions_model_idx ON speech_extractions (model_id);


-- entity_names: stage 5. One row for each distinct (norm_name, type).
-- scripts/link_entities.py links each name to one tag, or to no tag. One
-- decision serves every speech that holds the name.
--
-- norm_name is the name in lower case, with single spaces, without outer
-- punctuation. name is the most frequent spelling among the kept items.
-- link_status:
--   pending  no decision yet for the current version and tag set
--   linked   tag_id holds the tag
--   none     no tag fits, or the model was not sure enough
-- link_reason says why a linked row holds its link:
--   exact_match  the name has the same norm_name as exactly one tag name or
--                alias. No model call happened, and link_p is NULL.
--   model        the decision model decided. link_p is its probability.
-- A link is never written into tags.aliases. tags.aliases is part of the text
-- that each tag vector reads, so a new alias would move the search space.
-- tag_set_version is the largest tags.id at decision time. When new tags
-- arrive, a 'none' with an older version can get a new decision.
CREATE TABLE IF NOT EXISTS entity_names (
    id               BIGSERIAL PRIMARY KEY,
    norm_name        TEXT     NOT NULL,
    type             TEXT     NOT NULL,
    name             TEXT     NOT NULL,
    n_speeches       INTEGER  NOT NULL DEFAULT 0,  -- distinct speeches with a kept item of this name
    embedding_query  vector(1536),                  -- gemini-embedding-001, RETRIEVAL_QUERY, of name
    link_status      TEXT     NOT NULL DEFAULT 'pending' CHECK (link_status IN ('pending', 'linked', 'none')),
    tag_id           INTEGER  REFERENCES tags(id),
    link_p           REAL,                          -- the probability of the top option
    candidates       JSONB,                         -- the options, their source, and their probabilities
    link_raw         JSONB,                         -- the model answer before the checks
    link_warnings    TEXT[]   NOT NULL DEFAULT '{}',
    linked_by        TEXT,                          -- the model and the question version
    linked_at        TIMESTAMPTZ,
    tag_set_version  INTEGER,
    link_reason      TEXT     CHECK (link_reason IN ('exact_match', 'model')),
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (norm_name, type)
);
-- The linked names of one tag, for the page queries that find the speeches of a tag.
CREATE INDEX IF NOT EXISTS entity_names_tag_linked_idx ON entity_names (tag_id) WHERE link_status = 'linked';


-- speech_items: one row for each candidate subject of one speech. Stage 3
-- writes the LLM rows. scripts/add_candidates.py adds the other sources.
-- Stage 4 (scripts/judge_items.py) fills the judge columns, and stage 5 fills
-- entity_name_id.
--
-- source:
--   llm          the extraction model listed the item
--   dictionary   the entity dictionary found a known entity name in the speech
--                text, and the extraction did not list it (list = 'other')
--   summary_tag  a recognised tag: one of the tags nearest to the summary
--                vector of the speech (list = 'topic'). It is a tag already,
--                so tag_id holds it and stage 5 does not link it.
-- evidence is why an added row exists: the number of matches and the rank for a
-- dictionary row, the cosine distance and the rank for a summary tag. The
-- positions of added rows continue after the positions of the llm rows of the
-- same list.
-- model_salience is the 1 to 5 salience of the extraction model. It is stored
-- for comparison only. No decision uses it.
--
-- Stage 4 stores probabilities, so a new limit needs no new call: `kept` is
-- computed again from the stored values. judged_by names the model and the
-- question version. Each version fills its own columns, and the other columns
-- stay NULL.
--   q5 (current):
--     judge_subject_p  topics and recognised tags: P(true) of "X is a main or
--                      supporting subject of this speech, not only a passing
--                      mention".
--     judge_use_p      named items: P(absent), P(aside), P(point),
--                      P(other_meaning), in this order.
--   q4 (term 18 and the 2019 sample):
--     judge_level_p    topics and recognised tags: P(level 0) to P(level 3) of
--                      the centrality scale.
--     judge_role_p     named items: P(absent), P(aside), P(point).
--     judge_refers_p   named items: P(true) that the words of the speech name
--                      this one item without a guess.
--     judge_type_p     named items: the probability of each type.
--     judge_type       the model's type when its probability is 0.7 or more.
--                      Stage 5 uses it when it is set.
-- judge_state says what the model read: 'speech' (the speech text) or
-- 'summary' (the summary and the mentions, when the speech is too long).
CREATE TABLE IF NOT EXISTS speech_items (
    id               BIGSERIAL PRIMARY KEY,
    extraction_id    BIGINT   NOT NULL REFERENCES speech_extractions(id) ON DELETE CASCADE,
    speech_id        BIGINT   NOT NULL REFERENCES speeches(id),
    list             TEXT     NOT NULL CHECK (list IN ('topic', 'other')),
    position         SMALLINT NOT NULL,     -- 1 = first in the list
    name             TEXT     NOT NULL,
    type             TEXT     NOT NULL,
    model_salience   SMALLINT,
    mention          TEXT     NOT NULL,
    mention_found    BOOLEAN  NOT NULL,     -- the mention is in the speech text

    source           TEXT     NOT NULL DEFAULT 'llm' CHECK (source IN ('llm', 'dictionary', 'summary_tag')),
    tag_id           INTEGER  REFERENCES tags(id),
    evidence         JSONB,

    judge_subject_p  REAL,
    judge_use_p      REAL[],
    judge_level_p    REAL[],
    judge_role_p     REAL[],
    judge_refers_p   REAL,
    judge_type_p     JSONB,
    judge_type       TEXT,
    kept             BOOLEAN,
    judge_state      TEXT     CHECK (judge_state IN ('speech', 'summary')),
    judge_raw        JSONB,
    judge_warnings   TEXT[]   NOT NULL DEFAULT '{}',
    judged_by        TEXT,
    judged_at        TIMESTAMPTZ,

    entity_name_id   BIGINT   REFERENCES entity_names(id),

    UNIQUE (extraction_id, list, position),
    CONSTRAINT speech_items_summary_tag_has_tag CHECK ((source = 'summary_tag') = (tag_id IS NOT NULL))
);

CREATE INDEX IF NOT EXISTS speech_items_speech_idx ON speech_items (speech_id);
CREATE INDEX IF NOT EXISTS speech_items_entity_name_idx ON speech_items (entity_name_id);
-- The kept items of one tag, for the page queries that find the speeches of a tag.
CREATE INDEX IF NOT EXISTS speech_items_tag_kept_idx ON speech_items (tag_id) WHERE kept;


-- speech_summary_embeddings: one vector for the summary of one speech.
--
-- The embedding model turns the summary (speech_extractions.summary) into a
-- vector. pgvector measures the cosine distance between this vector and the tag
-- vectors. The nearest tags become the recognised tags of the speech.
--
-- The vector uses the task type RETRIEVAL_QUERY, so that it matches the tag
-- vectors of task type RETRIEVAL_DOCUMENT. The vector has length 1.
--
-- extraction_id is the primary key. When a new extraction replaces an old one,
-- ON DELETE CASCADE drops the old vector. input_hash is the md5 of the summary.
-- scripts/embed_summaries.py embeds a summary again only when the hash changes.
-- Summaries of 'rule-stub' are fixed texts and get no vector.
--
-- No vector index: one search compares one vector with a few thousand tag
-- vectors, and that scan takes milliseconds.
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


-- subjects: the specific subjects under the tags. A subject is a group of entity
-- names that mean one specific subject, for example "Sugarcane farmers' arrears"
-- under the tag Arrears. scripts/subject_join.py makes the subjects, and
-- scripts/load_subjects.py writes these rows. A speech has a subject when one of
-- its kept items has a name of that subject.
--
-- subject_key is the sorted list of entity name IDs, joined by spaces. It stays the
-- same when a rebuild makes the same subject. parent_tag_id is the tag that the
-- decision model chose for the subject (table subject_parents), or NULL when the
-- model chose no tag or did not decide the subject yet.
CREATE TABLE IF NOT EXISTS subjects (
    id             SERIAL  PRIMARY KEY,
    subject_key    TEXT    NOT NULL UNIQUE,
    label          TEXT    NOT NULL,
    label_source   TEXT    NOT NULL CHECK (label_source IN ('llm', 'llm_relabel', 'auto', 'name')),
    parent_tag_id  INTEGER REFERENCES tags(id),
    n_names        INTEGER NOT NULL,
    n_speeches     INTEGER NOT NULL,
    n_debates      INTEGER NOT NULL,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS subjects_parent_idx ON subjects (parent_tag_id);

-- subject_names: the entity names of each subject. A name is in one subject only.
CREATE TABLE IF NOT EXISTS subject_names (
    entity_name_id BIGINT  PRIMARY KEY REFERENCES entity_names(id),
    subject_id     INTEGER NOT NULL REFERENCES subjects(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS subject_names_subject_idx ON subject_names (subject_id);


-- subject_parents: the decision model's choice of a parent tag for each subject.
-- scripts/subject_parents.py writes these rows. The key is subject_key, not the
-- subject ID, so a decision stays when scripts/load_subjects.py loads the same
-- subject again. A subject has a parent only when one tag gets at least the link
-- probability. The options are the tags of the linked names of the subject and
-- the tags nearest to the centre of its name vectors.
CREATE TABLE IF NOT EXISTS subject_parents (
    subject_key      TEXT     PRIMARY KEY,
    parent_tag_id    INTEGER  REFERENCES tags(id),
    parent_p         REAL     NOT NULL,             -- the probability of the top option, also when it is NONE
    options          JSONB    NOT NULL,             -- each option: tag_id, tag, source, distance, p
    raw              JSONB,                         -- the model answer before the checks
    warnings         TEXT[]   NOT NULL DEFAULT '{}',
    decided_by       TEXT     NOT NULL,             -- the model and the question version
    tag_set_version  INTEGER  NOT NULL,
    decided_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

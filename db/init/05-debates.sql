-- debates: one row per debate transcript, as published by sansad.in.
--
-- A debate is identified by three numbers -- (loksabha, session, dbslno) -- and
-- that triple is the natural key. The corpus is ~64,911 debates across terms
-- 13-18. `scripts/import_debates.py` fills this table; see
-- internal_docs/022_DEBATE_IMPORT.md for the field mapping and the reasoning.
--
-- SOURCE OF TRUTH. `raw_html` is what we fetched and is never written by the
-- parser. Everything the parser produces (speeches, speaker resolution,
-- full_text) is derived and belongs in other tables, so a reparse never
-- touches this one. That is why there is no `is_legacy` or `full_text` column
-- here -- see the two notes below.
--
-- NO ERA COLUMN, DELIBERATELY. internal_docs/006_SCHEMA.md's original design had
-- `is_legacy BOOL`. One boolean cannot hold it: "is the Hindi disguised?" and
-- "are the speaker names bold or plain capitals?" are two independent questions,
-- and conflating them is a known bug (018 §6.9). Both are computable from
-- raw_html on demand -- but NOT by a plain SQL regex. See the next note.
-- Storing a derived answer would freeze today's guess at a question we are
-- still trying to measure.
--
-- ############################################################################
-- DO NOT GREP raw_html FOR FONT GLYPHS. It does not work, and it fails in the
-- most dangerous way available: quietly, with a confident small number.
--
-- These three lines used to live here as the recommended way to measure era
-- and font, and .claude/STATE.md called the query built from them "the
-- highest-value query in the project":
--     disguised Hindi (ISFOC): raw_html ~ 'BÉE|àÉ|ãÉ|ºÉ'
--     the second font:         raw_html ~ 'Eò|®ú|½þ'
-- They are WRONG. `raw_html` MIXES representations: this source stores most
-- old-font pages as HTML NAMED ENTITIES (&Eacute;, &Ograve;, &THORN;) and
-- Unicode Devanagari as NUMERIC entities (&#2358;), while a minority of pages
-- store the very same glyphs literally. A literal-glyph regex therefore sees
-- only the minority. Measured over all 64,921 rows:
--     LS13 old-font debates:  regex said 43     truth 4,443  (4,400 entity-only)
--     second font:            regex said  7     truth   370  (all in LS13)
-- The regex found 1% of the corpus and reported it as the whole. Note that
-- `SELECT count(*) ... WHERE raw_html LIKE '%श्री%'` returns ZERO across every
-- row in this table, which is the fastest way to see the problem for yourself.
--
-- The PARSER is not affected and never was: both readers go through
-- BeautifulSoup, which decodes entities before any matching happens. Only
-- hand-written SQL over raw_html is affected -- i.e. exactly the ad-hoc
-- measurement queries we reach for when deciding what to work on next.
--
-- TO MEASURE, decode first, in Python, the way the parser does:
--     html.unescape(raw_html)   then apply the signature
-- Routing itself is the one thing a plain regex CAN answer, because anchors
-- are pure ASCII -- and it is the real decision the code makes:
--     debate_fetch_legacy.looks_legacy(html) == not MODERN_ANCHOR_RE.search(html)
--     recent-style ID tag: raw_html ~* '<A\s+name="[0-9]+\*[0-9]+"'
-- ############################################################################
--
-- Two API responses feed this table and NEITHER is complete on its own: the
-- search record carries the title/type/keywords but its `debateDesc` is always
-- empty; the details payload carries the text but has no title. Verified over
-- 90 debates. The shred below is lossless -- the details payload rebuilds
-- exactly from these columns (20/20 round-trip).
CREATE TABLE IF NOT EXISTS debates (
    id               BIGSERIAL   PRIMARY KEY,

    -- Natural key: the three numbers that identify any debate in the record.
    loksabha         SMALLINT    NOT NULL REFERENCES lok_sabhas(number),
    session          SMALLINT    NOT NULL,
    dbslno           INTEGER     NOT NULL,

    -- The debate itself. Parser input; never parser output.
    -- '' is legitimate (some debates genuinely carry no text); a MISSING ROW
    -- means "not fetched yet". That distinction is what makes the import
    -- resumable, so raw_html is NOT NULL rather than nullable.
    raw_html         TEXT        NOT NULL,   -- payload.debateDesc
    mp_list_raw      JSONB       NOT NULL,   -- payload.mpPartDetailList: the debate's
                                             --   own member list, the parser's anchor
                                             --   list. Identical in both responses
                                             --   (90/90), so stored once. Entries are
                                             --   {mpName, mpCode, mpPartCode} -- there
                                             --   is NO constituency in this API.

    -- Metadata.
    title            TEXT,                   -- search.debateTitle
    debate_type      TEXT,                   -- search.debateTypeDesc, e.g. 'SPECIAL MENTION'
    debate_type_code SMALLINT,               -- search.debateType. CAUTION: `debateType`
                                             --   names DIFFERENT fields in the two
                                             --   responses -- an int here, but the
                                             --   *string* in the details payload
                                             --   (== debateTypeDesc, 36/36).
    debate_date      DATE,                   -- both responses agree (90/90)
    contents         TEXT,                   -- payload.contents: agenda/summary line
    keywords         TEXT[],                 -- search.keywordUsed
    member_names     TEXT[],                 -- search.memberName. Strictly poorer than
                                             --   mp_list_raw (no mpCodes; equal length
                                             --   in 70/72, shorter in 2). Kept only so
                                             --   the shred stays lossless.

    -- Provenance.
    source_url       TEXT        NOT NULL,
    raw_html_sha256  CHAR(64)    NOT NULL,   -- did the record change under us on refetch?
    fetched_at       TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- Any key the API returned that we did not model. Expected to stay '{}'.
    -- Key sets were stable over 90 debates, but that is 0.14% of the corpus, and
    -- this project's history is meeting a species it did not imagine. Without
    -- this, an unexpected key vanishes silently and only a refetch finds it;
    -- with it, `WHERE extra <> '{}'` turns an unknown unknown into a query.
    extra            JSONB       NOT NULL DEFAULT '{}',

    -- The invariant that earns its place: makes the import idempotent. A run
    -- that dies at debate 40,000 is resumed by re-running the whole thing
    -- (ON CONFLICT ... DO UPDATE). Without this, a retry silently duplicates
    -- rows and every count computed afterwards is wrong.
    CONSTRAINT debates_natural_key UNIQUE (loksabha, session, dbslno)
);

CREATE INDEX IF NOT EXISTS debates_date_idx     ON debates (debate_date);
CREATE INDEX IF NOT EXISTS debates_loksabha_idx ON debates (loksabha, session);

-- TODO (deferred, same reasoning as 04-speakers.sql): full-text and semantic
-- search over raw_html will want their own indexes. Not added now because
-- nothing reads them yet, and a GIN index over multi-GB of HTML is not free.

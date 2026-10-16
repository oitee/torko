-- debates: one row for each debate transcript, as sansad.in publishes it.
--
-- Three numbers identify a debate: (loksabha, session, dbslno). That triple is
-- the natural key. scripts/import_debates.py fills this table.
--
-- This table is the source of truth. raw_html is what the import fetched, and
-- the parser never writes it. Everything that the parser makes (turns,
-- speeches) is in other tables, so a new parse never changes this table.
--
-- There is no "old format" column. Two separate questions decide how to read a
-- page: "is the Hindi in the old font?" and "are the speaker names bold or in
-- plain capitals?". One column cannot hold both answers. The code computes them
-- from raw_html when it needs them.
--
-- ############################################################################
-- DO NOT SEARCH raw_html FOR FONT GLYPHS WITH SQL. The result is wrong, and it
-- looks right.
--
-- raw_html mixes two representations. Most old-font pages store the glyphs as
-- HTML named entities (&Eacute;, &Ograve;, &THORN;), and Unicode Devanagari is
-- stored as numeric entities (&#2358;). A minority of pages store the same
-- glyphs as plain characters. A regex on plain glyphs sees only the minority.
-- Measured over all 64,921 rows:
--     term 13 old-font debates:  a regex found 43    the truth is 4,443
--     the second old font:       a regex found 7     the truth is 370
-- For the same reason, `raw_html LIKE '%श्री%'` finds zero rows.
--
-- The parser is not affected: both readers use BeautifulSoup, which decodes the
-- entities first. To measure, decode in Python first:
--     html.unescape(raw_html), then apply the pattern
-- One question works in SQL, because its markers are plain ASCII: the format of
-- the page.
--     debate_fetch_legacy.looks_legacy(html) == not MODERN_ANCHOR_RE.search(html)
--     recent format: raw_html ~* '<A\s+name="[0-9]+\*[0-9]+"'
-- ############################################################################
--
-- Two API responses feed this table, and neither is complete alone. The search
-- record has the title, the type, and the keywords, but its debateDesc is
-- always empty. The details payload has the text but no title. The columns
-- below hold both without loss: the details payload can be rebuilt from them.
CREATE TABLE IF NOT EXISTS debates (
    id               BIGSERIAL   PRIMARY KEY,

    -- The natural key.
    loksabha         SMALLINT    NOT NULL REFERENCES lok_sabhas(number),
    session          SMALLINT    NOT NULL,
    dbslno           INTEGER     NOT NULL,

    -- The debate text. '' is a real value: some debates have no text. A missing
    -- row means "not fetched yet". The import uses that difference to continue
    -- after a stop, so raw_html is NOT NULL.
    raw_html         TEXT        NOT NULL,   -- payload.debateDesc
    mp_list_raw      JSONB       NOT NULL,   -- payload.mpPartDetailList: the debate's own
                                             --   member list, the parser's anchor list.
                                             --   Entries are {mpName, mpCode, mpPartCode}.
                                             --   This API gives no constituency.

    -- Metadata.
    title            TEXT,                   -- search.debateTitle
    debate_type      TEXT,                   -- search.debateTypeDesc, for example 'SPECIAL MENTION'
    debate_type_code SMALLINT,               -- search.debateType. CAUTION: the details payload
                                             --   uses the same name for the text type.
    debate_date      DATE,
    contents         TEXT,                   -- payload.contents: the agenda or summary line
    keywords         TEXT[],                 -- search.keywordUsed: the sansad.in keywords
    member_names     TEXT[],                 -- search.memberName. Poorer than mp_list_raw
                                             --   (no codes). Kept so that no field is lost.

    -- Provenance.
    source_url       TEXT        NOT NULL,
    raw_html_sha256  CHAR(64)    NOT NULL,   -- shows if the record changed on a new fetch
    fetched_at       TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- Any key of the API answer that no column holds. Expected to stay '{}'.
    -- `WHERE extra <> '{}'` finds an unexpected key.
    extra            JSONB       NOT NULL DEFAULT '{}',

    -- The natural key makes the import idempotent: a new run updates the rows
    -- that exist (ON CONFLICT ... DO UPDATE) and never duplicates them.
    CONSTRAINT debates_natural_key UNIQUE (loksabha, session, dbslno)
);

CREATE INDEX IF NOT EXISTS debates_date_idx     ON debates (debate_date);
CREATE INDEX IF NOT EXISTS debates_loksabha_idx ON debates (loksabha, session);

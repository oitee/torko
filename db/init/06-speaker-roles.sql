-- speaker_roles: the speaker labels that are NOT a person.
--
-- Two kinds of printed label name no single human being:
--   presiding -- the Chair, printed by office ("MR. SPEAKER:", "अध्यक्ष महोदय:").
--                131,641 turns across the corpus -- by a wide margin the largest
--                unattributed category we have.
--   crowd     -- an anonymous interjection ("SEVERAL HON. MEMBERS:",
--                "अनेक माननीय सदस्य:"). 1,199 turns.
--
-- NOT IN `persons`, DELIBERATELY, AND NOT GIVEN A sansad_id. This is the whole
-- point of a separate table. `MR. SPEAKER` spans LS13-18 and is therefore at
-- least five different human beings (Balayogi, Chatterjee, Meira Kumar,
-- Mahajan, Birla). A single row in `persons` would assert those five are one
-- person -- manufacturing, by hand, the exact identical-names ceiling that
-- STATE calls unfixable for `Chandra Shekhar`. And the query this whole project
-- exists to answer is "gather one MP's speeches across twenty years", which a
-- pseudo-person in `persons` poisons silently and permanently. A role has no
-- sansad_id because a role is not a person and never acquires one.
--
-- WHY `kind` EXISTS -- the two are not the same thing and must not be merged.
-- A crowd label names nobody, in principle, forever: it is terminal, and no
-- future work can ever resolve it. A presiding officer IS a knowable human --
-- who chaired a given sitting is a matter of historical record -- so those
-- 131,641 turns are recoverable later by joining a Speaker-tenure table
-- (date -> who presided) onto this one. Storing both under one undifferentiated
-- kind would forfeit that recovery, or cost a migration to get it back.
-- `resolvable` records that asymmetry as data rather than as folklore.
--
-- These rows are canonical OFFICES, not label spellings. The corpus prints 143
-- distinct role strings ("MR.SPEAKER", "HON . SPEAKER", "HON. DEPUPTY-SPEAKER",
-- "*m75 HON. CHAIRPERSON"), but that tail is spacing/punctuation/typo noise
-- carrying no attribution information, and `is_presiding_label` already absorbs
-- it by searching for the office word rather than matching whole strings. The
-- Devanagari forms are the SAME offices, not extra ones: अध्यक्ष = Speaker,
-- उपाध्यक्ष = Deputy Speaker, सभापति = Chairman.
CREATE TABLE IF NOT EXISTS speaker_roles (
    id           SMALLSERIAL PRIMARY KEY,

    -- Stable slug the parser emits as `roleCode`. Never renumber these: they
    -- are what derived speech rows point at.
    code         TEXT NOT NULL UNIQUE,

    kind         TEXT NOT NULL CHECK (kind IN ('presiding', 'crowd')),
    display_name TEXT NOT NULL,

    -- Can this label ever be resolved to a specific human being? presiding:
    -- yes, in principle, via a future tenure table. crowd: no, ever. This is a
    -- statement about the world, not about our current code.
    resolvable   BOOLEAN NOT NULL,

    notes        TEXT
);

INSERT INTO speaker_roles (code, kind, display_name, resolvable, notes) VALUES
    ('speaker', 'presiding', 'Speaker', TRUE,
     'अध्यक्ष / अध्यक्ष महोदय / MR./MADAM/HON. SPEAKER. One person per term; the page does not name them, which is why they must come from a tenure table.'),
    ('deputy_speaker', 'presiding', 'Deputy Speaker', TRUE,
     'उपाध्यक्ष / MR. DEPUTY-SPEAKER. Matched before `speaker` -- the string contains it.'),
    ('chairman', 'presiding', 'Chairman', TRUE,
     'सभापति / MR./MADAM CHAIRMAN / HON. CHAIRPERSON. Unlike the Speaker this office rotates among a panel of MPs during a sitting, which is why the page sometimes prints the name alongside it -- see the 140 role+person labels.'),
    ('deputy_chairman', 'presiding', 'Deputy Chairman (Rajya Sabha)', TRUE,
     'DEPUTY-CHAIRMAN (RAJYA SABHA). 58 occurrences, LS13 and LS15: the OTHER House''s presiding officer appearing in a Lok Sabha transcript. Its own office, not a spelling of `chairman` -- a different human entirely. Matched before `chairman`, which its string contains. NOTE: the "(RAJYA SABHA)" suffix is a CHAMBER, not a person, so any future rule that reads a name out of a role label''s parentheses must exclude this form or it will invent a member called "Rajya Sabha".'),
    ('members_crowd', 'crowd', 'Several/Some Hon. Members', FALSE,
     'SEVERAL/SOME/MANY HON. MEMBERS, अनेक/कई/कुछ माननीय सदस्य. Deliberately ONE row: several-vs-some carries no attribution information, so splitting them would invent a distinction the data does not make.')
ON CONFLICT (code) DO NOTHING;

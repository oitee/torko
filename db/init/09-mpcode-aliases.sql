-- mpcode_aliases: a translation table, NOT a roster.
--
-- The debate transcripts identify a speaker with a number they call `mpCode`
-- (the <A name="mpCode*part"> anchor / mpPartDetailList). Our roster identifies
-- a person with a number the member directory calls `mpsno`, stored as
-- persons.sansad_id. These are TWO DIFFERENT numbering systems (see
-- internal_docs 033). They overlap -- the same number is usually the same
-- person, which is why anchor resolution works ~121k times -- but they also
-- COLLIDE: mpCode 572 = H.D. Deve Gowda in a debate, but mpsno 572 = Taherali
-- Abdullabhai (a 1st-Lok-Sabha member). mpCode 542 = Arun Jaitley; mpsno 542 =
-- Usha Verma.
--
-- So a speaker the source anchored under an mpCode that is NOT that person's
-- mpsno has no persons row and renders "unverified", even though the person is
-- in the roster under a different code (Sudip: anchored 4495, roster mpsno 38).
--
-- This table bridges that gap: mp_code -> person. It lives BESIDE persons, never
-- inside it -- inserting a persons row for these codes would duplicate a person
-- we already hold, or (on a colliding code) invent a second identity.
--
-- NEVER-GUESS: a row exists only when the SOURCE's own printed name labels for
-- that code, folded, point to exactly ONE person in the roster. Codes whose
-- labels name two different people are dropped, not resolved (see
-- scripts/populate_mpcode_aliases.py). The synthetic minister block (mpCode >=
-- 10000) is excluded wholesale -- those are minister role-slots the source
-- reuses across different humans (10008 = Ravi Shankar Prasad AND Anbumani
-- Ramadoss), not per-person codes, so no single person can own one.
--
-- Applied by hand, same as 06/07/08 (the init dir only auto-runs on a fresh
-- volume).
CREATE TABLE IF NOT EXISTS mpcode_aliases (
    mp_code        TEXT PRIMARY KEY,               -- the debate anchor code (turns.mp_code)
    person_id      INT  NOT NULL REFERENCES persons(id),
    evidence_turns INT  NOT NULL,                  -- turns whose folded name label backed this
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS mpcode_aliases_person_idx ON mpcode_aliases (person_id);

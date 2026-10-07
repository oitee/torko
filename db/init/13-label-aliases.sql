-- label_aliases: a speaker label that names one member, for turns that the
-- parser could not link to a member.
--
-- A label is the speaker name as the transcript prints it before a turn, for
-- example "डॉ. सत्यपाल सिंह ( बागपत )". The parser links most labels to a member
-- through the member code or the roster names. Some labels stay unlinked,
-- mostly labels in Hindi or Urdu script. An LLM chose one member from the
-- roster for each such label, and a person reviewed a sample of the answers.
--
-- The key is the Lok Sabha term plus the exact label, after the removal of
-- extra spaces. A label that differs by one character does not match, and a
-- row for one term never applies in another term.
--
-- scripts/populate_turns.py uses a row only when the parser found no member and
-- no chair role for the turn. A row never overrides the parser. Such a turn has
-- name_source 'label-alias'.
--
-- The rows cannot be rebuilt from the debates. Their source is the tracked file
-- data/label_aliases.tsv, and scripts/load_label_aliases.py loads it.
--
-- Applied by hand on an existing volume (the init folder runs only on a fresh
-- volume).
CREATE TABLE IF NOT EXISTS label_aliases (
    loksabha      SMALLINT NOT NULL REFERENCES lok_sabhas(number),
    speaker_label TEXT     NOT NULL,   -- the label after normalize_label()
    person_id     INT      NOT NULL REFERENCES persons(id),
    basis         TEXT     NOT NULL,   -- name_and_constituency, name, constituency, office
    source        TEXT     NOT NULL,   -- how the row was made and checked
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (loksabha, speaker_label)
);

CREATE INDEX IF NOT EXISTS label_aliases_person_idx ON label_aliases (person_id);

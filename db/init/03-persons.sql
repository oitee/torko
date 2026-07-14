-- persons: one row per real human MP -- our own stable identity, the cross-term
--
-- id        internal identity. Maps to mpCode 1-1
-- sansad_id the sansad.in mpCode. Stable per-person across terms
--           UNIQUE here (1-1 with a person), but deliberately NOT the PK.
CREATE TABLE IF NOT EXISTS persons (
    id          SERIAL PRIMARY KEY,
    name        TEXT NOT NULL,          -- canonical / display name
    sansad_id   INT  UNIQUE             -- mpCode - from sasad API
);

-- speech_party_mv: the party, seat, and state of the member of each speech, at the date of the debate. One row for each speech.
-- The rule: the seat record of the member in the term of the debate with the latest start on or before the debate date.
-- A speech with no member, or with no seat record, has NULL in party, seat, and state.
--
-- The view does not update itself. scripts/refresh_speech_tags.py fills it again, after each change to speeches,
-- speakers, or parties. scripts/build_tag_related.py runs that script first.
-- The unique index lets REFRESH MATERIALIZED VIEW CONCURRENTLY run while the pages read the old rows.

CREATE MATERIALIZED VIEW IF NOT EXISTS speech_party_mv AS
SELECT s.id AS speech_id, pa_party.code AS party, pa_row.seat, pa_row.state
FROM speeches s
JOIN debates d ON d.id = s.debate_id
LEFT JOIN LATERAL (
    SELECT sp.party_id, sp.constituency AS seat, st.name AS state
    FROM speakers sp LEFT JOIN states st ON st.id = sp.state_id
    WHERE sp.person_id = s.person_id AND sp.lok_sabha_term = d.loksabha
      AND sp.effective_from <= COALESCE(d.debate_date, sp.effective_from)
    ORDER BY sp.effective_from DESC LIMIT 1
) pa_row ON true
LEFT JOIN parties pa_party ON pa_party.id = pa_row.party_id;

CREATE UNIQUE INDEX IF NOT EXISTS speech_party_mv_speech_key ON speech_party_mv (speech_id);

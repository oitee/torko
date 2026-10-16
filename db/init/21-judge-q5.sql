-- Stage 4 question version q5 asks two questions in place of the four of q4.
--
-- judge_subject_p: topics and recognised tags. The probability that the
--                  statement "X is a main or supporting subject of this speech,
--                  not only a passing mention" is true.
-- judge_use_p:     named items. The probabilities of the four answers to "How
--                  does this speech use X?", in this order: absent, aside,
--                  point, other_meaning.
--
-- Rows judged with q4 keep judge_level_p, judge_role_p, and judge_refers_p.
-- A row judged with q5 has those columns NULL. judged_by names the version.
ALTER TABLE speech_items
    ADD COLUMN IF NOT EXISTS judge_subject_p REAL,
    ADD COLUMN IF NOT EXISTS judge_use_p     REAL[];

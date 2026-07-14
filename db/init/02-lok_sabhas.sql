-- lok_sabhas: one row per Lok Sabha term
-- Current Scope: We will have terms from 13 till 18 for now as
-- data is available only for these years. We seed them manually

-- Dates are manually added for now; can later be done automatically
-- if more sessions are there
CREATE TABLE IF NOT EXISTS lok_sabhas (
    number      INT  PRIMARY KEY,
    start_date  DATE,
    end_date    DATE
);

INSERT INTO lok_sabhas (number,start_date,end_date) VALUES
    (13,'1999-10-20','2004-02-06'), 
    (14, '2004-06-02', '2009-05-18'),
    (15, '2009-06-01', '2014-05-18'),
    (16, '2014-06-04', '2019-05-24'),
    (17, '2019-06-17', '2024-06-05'),
    (18, '2024-06-24', NULL)
ON CONFLICT (number) DO NOTHING;

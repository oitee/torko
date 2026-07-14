-- Runs automatically the first time the db container initialises an empty
-- data dir. Enables the two extensions the schema depends on (see SCHEMA.md).
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

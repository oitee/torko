-- The files in this folder build the whole schema on an empty database.
--
-- docker-compose.yml mounts this folder as /docker-entrypoint-initdb.d. Postgres
-- runs the files in name order, one time only, when the container starts with an
-- empty data volume. An existing volume never runs them again.
--
-- Each file shows the CURRENT shape of its tables. There are no ALTER files.
-- To change the schema:
--   1. Edit the CREATE statement in the file of that area.
--   2. Run the matching ALTER statement by hand on each existing database.
-- A production server gets a copy of a whole database (schema and data
-- together), so it never needs the ALTER statements.
--
-- The files:
--   01-extensions.sql          the two extensions
--   02-members.sql             terms, members, parties, chair roles, label fixes
--   03-debates.sql             the debates as fetched from sansad.in
--   04-speeches-and-turns.sql  the parser output: speeches and turns
--   05-tags.sql                the tag list and the tag vectors
--   06-tag-pipeline.sql        the tag pipeline: extractions, candidates, links

-- vector: the pgvector type for embeddings.
-- pg_trgm: trigram matching for names.
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

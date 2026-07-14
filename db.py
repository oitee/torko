"""
Database connection helper (SQLAlchemy Core).

We use SQLAlchemy Core -- not the ORM -- so the SQL stays visible and explicit
in the scripts (see internal_docs/006_SCHEMA.md, which commits the app to
SQLAlchemy). One engine, built from environment variables that default to the
docker-compose.yml credentials so `docker compose up` + these scripts just work
out of the box.
"""
from __future__ import annotations

import os

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


def database_url() -> str:
    """
    Build the Postgres URL. A full DATABASE_URL wins if set; otherwise assemble
    it from the same POSTGRES_* vars docker-compose.yml uses (defaults: user
    postgres, db torko, no password under trust auth).
    """
    if url := os.environ.get("DATABASE_URL"):
        return url
    user = os.environ.get("POSTGRES_USER", "postgres")
    password = os.environ.get("POSTGRES_PASSWORD", "")
    host = os.environ.get("POSTGRES_HOST", "localhost")
    port = os.environ.get("POSTGRES_PORT", "5432")
    name = os.environ.get("POSTGRES_DB", "torko")
    credentials = f"{user}:{password}" if password else user
    return f"postgresql+psycopg://{credentials}@{host}:{port}/{name}"


def get_engine() -> Engine:
    """A configured SQLAlchemy engine. `future=True` = 2.0-style semantics."""
    return create_engine(database_url(), future=True)

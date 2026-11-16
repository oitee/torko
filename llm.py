"""Shared parts of the LLM steps: the table of model names."""
from sqlalchemy import text


def model_id(conn, name: str) -> int:
    """The id of the model name. A new name is added to the table models.

    The function reads first. An INSERT with ON CONFLICT uses one number of the SMALLINT sequence on each call,
    also when the name exists, so many calls would use up the sequence.
    """
    found = conn.execute(text("SELECT id FROM models WHERE name = :n"), {"n": name}).scalar()
    if found is not None:
        return found
    conn.execute(text("INSERT INTO models (name) VALUES (:n) ON CONFLICT (name) DO NOTHING"), {"n": name})
    return conn.execute(text("SELECT id FROM models WHERE name = :n"), {"n": name}).scalar()

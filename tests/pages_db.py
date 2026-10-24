"""A read-only database connection for the page tests. A test that uses it skips when the database is not reachable."""
import pytest


@pytest.fixture(scope="module")
def page_conn():
    from pages.common import engine
    try:
        conn = engine().connect()
    except Exception as exc:  # no database on this machine
        pytest.skip(f"no database: {exc!s:.80}")
    yield conn
    conn.close()

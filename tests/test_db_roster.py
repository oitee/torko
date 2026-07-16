"""
db_roster.load_db_roster: the last-resort DB roster fallback.

Kept offline like every other test in this suite -- no test here touches a real
Postgres. `db.get_engine` is monkeypatched with a fake engine/connection so we
can assert (a) the query scopes by lok_sabha_term >= term, not ==, and (b) any
connection/query failure is swallowed into an empty list rather than raised,
which is what lets debate_fetch.py keep working with no Postgres running.
"""
from types import SimpleNamespace

import db_roster


class _FakeConn:
    """Records the SQL text handed to execute() and returns canned rows."""

    def __init__(self, rows):
        self.rows = rows
        self.captured_sql = None
        self.captured_params = None

    def execute(self, stmt, params):
        self.captured_sql = str(stmt)
        self.captured_params = params
        return SimpleNamespace(all=lambda: self.rows)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class _FakeEngine:
    def __init__(self, rows):
        self._conn = _FakeConn(rows)

    def connect(self):
        return self._conn


class TestLoadDbRoster:
    def test_query_scopes_by_greater_than_or_equal_not_equality(self, monkeypatch):
        fake_engine = _FakeEngine(rows=[])
        monkeypatch.setattr("db.get_engine", lambda: fake_engine)

        db_roster.load_db_roster(15)

        assert ">=" in fake_engine._conn.captured_sql
        assert "= :term" not in fake_engine._conn.captured_sql.replace(">=", "")
        assert fake_engine._conn.captured_params == {"term": 15}

    def test_returns_mpcode_mpname_shape_from_rows(self, monkeypatch):
        rows = [
            SimpleNamespace(mp_code=9, mp_name="Shri Mohan Singh"),
            SimpleNamespace(mp_code=42, mp_name="Shri Someone Else"),
        ]
        fake_engine = _FakeEngine(rows=rows)
        monkeypatch.setattr("db.get_engine", lambda: fake_engine)

        roster = db_roster.load_db_roster(13)

        assert roster == [
            {"mpCode": "9", "mpName": "Shri Mohan Singh"},
            {"mpCode": "42", "mpName": "Shri Someone Else"},
        ]

    def test_connection_failure_returns_empty_list_not_raise(self, monkeypatch):
        def boom():
            raise RuntimeError("no postgres running")

        monkeypatch.setattr("db.get_engine", boom)

        assert db_roster.load_db_roster(18) == []

    def test_query_failure_returns_empty_list_not_raise(self, monkeypatch):
        class _BoomConn:
            def execute(self, *a, **k):
                raise RuntimeError("relation \"speakers\" does not exist")

            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

        fake_engine = SimpleNamespace(connect=lambda: _BoomConn())
        monkeypatch.setattr("db.get_engine", lambda: fake_engine)

        assert db_roster.load_db_roster(18) == []

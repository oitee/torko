from scripts.refresh_speech_tags import refresh


class FakeConn:
    def __init__(self):
        self.sql = []

    def execute(self, stmt):
        self.sql.append(str(stmt))
        return self

    def scalar(self):
        return 7


def test_refresh_keeps_old_rows_readable_and_updates_statistics():
    conn = FakeConn()
    assert refresh(conn) == 7
    assert conn.sql[:4] == ["REFRESH MATERIALIZED VIEW CONCURRENTLY speech_tags_mv", "ANALYZE speech_tags_mv",
                            "REFRESH MATERIALIZED VIEW CONCURRENTLY speech_party_mv", "ANALYZE speech_party_mv"]

import contextlib
import json

import pages.prebuilt as pb
from scripts import build_snapshots


def fake_builders(calls):
    return lambda: {"home": lambda conn: calls.append(conn) or {"b": 2, "a": "é"}}


def test_write_gives_the_bytes_of_jsonify_and_a_readable_file(tmp_path):
    data = pb.write("home", {"b": 2, "a": "é"}, tmp_path)
    assert data == pb.to_bytes({"b": 2, "a": "é"})
    assert json.loads(data) == {"b": 2, "a": "é"}
    assert pb.read("home", tmp_path) == data
    assert (tmp_path / "home.json").stat().st_mode & 0o777 == 0o644
    assert [p.name for p in tmp_path.iterdir()] == ["home.json"]  # no temporary file stays


def test_read_of_an_absent_file_is_none(tmp_path):
    assert pb.read("home", tmp_path) is None


def test_send_builds_and_writes_an_absent_file_then_reads_it(tmp_path, monkeypatch, caplog):
    calls = []
    monkeypatch.setattr(pb, "builders", fake_builders(calls))
    connect = lambda: contextlib.nullcontext("conn")  # noqa: E731
    r = pb.send("home", connect, tmp_path)
    assert r.status_code == 200 and r.mimetype == "application/json"
    assert json.loads(r.get_data()) == {"b": 2, "a": "é"}
    assert calls == ["conn"] and "absent" in caplog.text
    pb.send("home", connect, tmp_path)
    assert calls == ["conn"]  # the second request reads the file and does not build


def test_send_uses_no_connection_when_the_file_exists(tmp_path):
    pb.write("home", {"x": 1}, tmp_path)

    def connect():
        raise AssertionError("no connection expected")
    assert json.loads(pb.send("home", connect, tmp_path).get_data()) == {"x": 1}


def test_route_carries_its_page_module_for_the_api_docs():
    r = pb.prebuilt_route("home_featured")
    assert r.prebuilt == "home_featured" and r.page_module == "pages.home_featured"


def test_to_bytes_is_the_same_as_jsonify():
    import datetime
    import decimal

    from flask import Flask, jsonify
    answer = {"b": [1, 2.5, None], "a": "é", "d": datetime.date(2024, 8, 8), "n": decimal.Decimal("1.50")}
    with Flask(__name__).app_context():
        assert pb.to_bytes(answer) == jsonify(answer).get_data()


def test_two_first_requests_at_the_same_time_build_one_time(tmp_path, monkeypatch):
    import threading
    import time
    calls = []

    def slow(conn):
        calls.append(conn)
        time.sleep(0.05)
        return {"x": 1}
    monkeypatch.setattr(pb, "builders", lambda: {"home": slow})
    connect = lambda: contextlib.nullcontext("conn")  # noqa: E731
    threads = [threading.Thread(target=pb.send, args=("home", connect, tmp_path)) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert calls == ["conn"]


def test_build_all_builds_the_named_answers(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(pb, "builders", fake_builders(calls))
    sizes = build_snapshots.build_all("conn", ["home"], built_dir=tmp_path)
    assert sizes == {"home": len((tmp_path / "home.json").read_bytes())}

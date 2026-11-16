"""Answers that are built once at the rebuild and sent from a file, with no database call per request.

Each name in SNAPSHOTS is one API answer with no request parameters. scripts/build_snapshots.py writes
data/built/<name>.json. The route reads that file and sends its bytes as they are.

When the file is absent, the route logs a warning, builds the answer from the database, writes the file,
and sends it. So a forgotten build makes only the first request slow. It does not break the page.

The file holds the same bytes that jsonify sends with the default settings of Flask (sorted keys, ASCII only,
no spaces, one newline at the end). So the answer does not change when a route moves to a file.
"""
import datetime
import decimal
import json
import logging
import os
import pathlib
import tempfile
import threading
import uuid

from flask import Response
from werkzeug.http import http_date

BUILT_DIR = pathlib.Path(__file__).resolve().parent.parent / "data" / "built"
log = logging.getLogger(__name__)
_build_lock = threading.Lock()


def builders():
    """Return name -> function(conn) that builds the answer. The import is here to avoid an import loop."""
    from pages.home import home_answer
    from pages.home_featured import home_featured
    from pages.method import method_page
    return {"home": home_answer, "home_featured": home_featured, "method": lambda conn: method_page(conn, None)}


def _json_default(value):
    """The values that the JSON module cannot write, written as the default JSON provider of Flask writes them."""
    if isinstance(value, datetime.date):
        return http_date(value)
    if isinstance(value, (decimal.Decimal, uuid.UUID)):
        return str(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def to_bytes(answer):
    """Return the bytes that jsonify sends for the answer."""
    return (json.dumps(answer, default=_json_default, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def path_of(name, built_dir=None):
    return pathlib.Path(built_dir or BUILT_DIR) / f"{name}.json"


def write(name, answer, built_dir=None):
    """Write the answer to its file in one atomic step. A reader never sees a half-written file. Return the bytes."""
    data = to_bytes(answer)
    path = path_of(name, built_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        os.chmod(tmp, 0o644)  # mkstemp makes the file readable by its owner only
        os.replace(tmp, path)
    except BaseException:
        pathlib.Path(tmp).unlink(missing_ok=True)
        raise
    return data


def build(conn, name, built_dir=None):
    """Build one answer from the database and write its file. Return the bytes."""
    return write(name, builders()[name](conn), built_dir)


def read(name, built_dir=None):
    """Return the bytes of the file, or None when the file is absent."""
    try:
        return path_of(name, built_dir).read_bytes()
    except FileNotFoundError:
        return None


def send(name, connect, built_dir=None):
    """Return the response for the name. connect() opens a database connection, only for the fallback build."""
    data = read(name, built_dir)
    if data is None:
        with _build_lock:  # two first requests at the same time build the answer one time
            data = read(name, built_dir)
            if data is None:
                log.warning("prebuilt answer %s is absent, building it now", name)
                with connect() as conn:
                    data = build(conn, name, built_dir)
    return Response(data, mimetype="application/json")


def prebuilt_route(name):
    """Return a route function that sends the prebuilt answer. pages_api calls it with no connection."""
    def route(args=None):
        from pages_api import get_engine
        return send(name, get_engine().connect)
    route.prebuilt = name
    route.__name__ = f"prebuilt_{name}"
    route.page_module = f"pages.{name}"  # each name is also its page module, so the API docs show the summary of that page
    return route

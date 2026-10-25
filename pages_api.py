"""The JSON routes of the public pages, as one Flask blueprint.

Each module in PAGES lives in the package pages/ and defines ROUTES: a list of (rule, function) pairs.
Each function takes a read-only connection and the route arguments, and returns a dict, or None when the
key is unknown (the route then answers 404). A module that does not exist yet is skipped.
"""
import importlib

from flask import Blueprint, abort, jsonify, request

from pages.common import engine

PAGES = ["home", "tag", "member", "place", "speech", "debate", "party", "compare", "trends", "today", "my_mp"]

bp = Blueprint("pages", __name__, url_prefix="/api")
_engine = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = engine()
    return _engine


def _view(fn):
    def view(**kw):
        with get_engine().connect() as conn:
            out = fn(conn, **kw, args=request.args)
        if out is None:
            abort(404)
        return jsonify(out)
    view.__name__ = f"{fn.__module__}.{fn.__name__}".replace(".", "_")
    view.page_module = fn.__module__
    return view


def register(blueprint=bp, pages=PAGES):
    loaded = []
    for name in pages:
        try:
            mod = importlib.import_module(f"pages.{name}")
        except ModuleNotFoundError as exc:
            if exc.name == f"pages.{name}":
                continue
            raise
        for rule, fn in mod.ROUTES:
            blueprint.add_url_rule(rule, view_func=_view(fn))
        loaded.append(name)
    return loaded

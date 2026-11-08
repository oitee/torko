"""The OpenAPI description of the JSON routes, and a browser page (Swagger UI) to call them.

/api/openapi.json is built from the route table of the app, so a new route appears in it with no extra work.
The query arguments are not in the route table, so QUERY lists them by path.
/api/docs/ serves Swagger UI from the package swagger_ui_bundle. The page loads no file from the internet.
The two addresses are for local work only. The app has them only when API_DOCS=true is in the environment.
"""
import importlib
import os
import re

from flask import Blueprint, current_app, jsonify, send_from_directory
from swagger_ui_bundle import swagger_ui_path

bp = Blueprint("openapi", __name__)


def enabled(env=None):
    """True only when API_DOCS is "true". With no value, the docs are off, so a public server never shows them."""
    env = os.environ if env is None else env
    return env.get("API_DOCS", "false").strip().lower() == "true"


def register(app, env=None):
    """Add the docs addresses to the app when enabled(env) is true. Return True when it added them."""
    if not enabled(env):
        return False
    app.register_blueprint(bp)
    return True

TYPES = {"IntegerConverter": "integer", "FloatConverter": "number"}

# path: [(name, type, required, description)]
QUERY = {
    "/api/compare": [
        ("kind", "string", True, "member or party."),
        ("a", "string", True, "A member id when kind=member. A party code when kind=party."),
        ("b", "string", True, "A member id when kind=member. A party code when kind=party."),
        ("terms", "string", False, "A comma list of Lok Sabha numbers, for example 17,18."),
    ],
    "/api/my-mp": [("q", "string", True, "A part of the seat name, case-insensitive.")],
    "/api/speeches": [
        ("member", "string", False, "A comma list of member ids (persons.id)."),
        ("member_not", "string", False, "A comma list of member ids to leave out."),
        ("tag", "string", False, "A comma list of tag slugs. A speech needs all of them. A merged tag opens its kept tag."),
        ("tag_any", "string", False, "A comma list of tag slugs. A speech needs one of them."),
        ("tag_not", "string", False, "A comma list of tag slugs to leave out. A speech with no tags stays."),
        ("subject", "string", False, "A comma list of subject ids."),
        ("subject_not", "string", False, "A comma list of subject ids to leave out."),
        ("place", "string", False, "A comma list of place tag slugs. A speech needs one of them."),
        ("place_not", "string", False, "A comma list of place tag slugs to leave out."),
        ("term", "string", False, "A comma list of Lok Sabha numbers, for example 17,18."),
        ("session", "string", False, "A comma list of term-session pairs, for example 17-15,18-1."),
        ("term_not", "string", False, "A comma list of Lok Sabha numbers to leave out."),
        ("session_not", "string", False, "A comma list of term-session pairs to leave out."),
        ("kind", "string", False, "A comma list of speech kinds: zero_hour, rule_377, bill, budget, discussion, statement, other."),
        ("kind_not", "string", False, "A comma list of speech kinds to leave out."),
        ("party", "string", False, "A comma list of party codes, the party of the member on the date of the debate."),
        ("party_not", "string", False, "A comma list of party codes to leave out."),
        ("state", "string", False, "A comma list of state names, the state of the member on the date of the debate."),
        ("state_not", "string", False, "A comma list of state names to leave out."),
        ("seat", "string", False, "A comma list of seat names, the seat of the member on the date of the debate."),
        ("seat_not", "string", False, "A comma list of seat names to leave out."),
        ("lang", "string", False, "A comma list of languages of the speech: en, hi, mixed. Only speeches with a summary have a language."),
        ("lang_not", "string", False, "A comma list of languages to leave out."),
        ("date_from", "string", False, "The first debate date, YYYY-MM-DD."),
        ("date_to", "string", False, "The last debate date, YYYY-MM-DD."),
        ("title", "string", False, "A text that the debate title holds."),
        ("title_not", "string", False, "A text that the debate title does not hold."),
        ("min_words", "integer", False, "The smallest word count of a speech."),
        ("max_words", "integer", False, "The largest word count of a speech."),
        ("q", "string", False, "Words to find in the member's own turns of the speech. Every word must be in one turn."),
        ("sort", "string", False, "best (default with q, not for exact words in quote marks), latest (default with no q), oldest, or longest."),
        ("page", "integer", False, "The page number. The default is 1."),
        ("per_page", "integer", False, "The rows on each page, from 1 to 50. The default is 20."),
        ("facets", "string", False, "1 adds the counts for each filter value. A comma list can also name tag, tag_all, state, seat, lang, member, place or subject_all."),
        ("group", "string", False, "member gives one row for each member, not for each speech."),
    ],
    "/api/tag/{slug}": [("term", "integer", False, "A Lok Sabha number. Parties, members and speech lists count only that term.")],
    "/api/today": [("date", "string", False, "A calendar day as YYYY-MM-DD. The default is today.")],
    "/api/search": [("q", "string", True, "The search text.")],
    "/api/distribution": [
        ("loksabha", "integer", True, "The Lok Sabha number."),
        ("session", "integer", True, "The session number."),
        ("dbslno", "integer", True, "The debate number of the official site."),
    ],
    "/api/dashboard/debates": [
        ("page", "integer", False, "The page number. The default is 1."),
        ("pageSize", "integer", False, "The rows on each page, from 1 to 100. The default is 20."),
        ("date_from", "string", False, "The first debate date, YYYY-MM-DD."),
        ("date_to", "string", False, "The last debate date, YYYY-MM-DD."),
        ("loksabha", "integer", False, "The Lok Sabha number."),
        ("session", "integer", False, "The session number."),
        ("party", "string", False, "A party code. Repeat it for more than one party."),
        ("speaker", "string", False, "A sansad_id. Repeat it for more than one member."),
        ("q", "string", False, "A part of the debate title."),
        ("debate_type", "string", False, "A debate type. Repeat it for more than one type."),
        ("text", "string", False, "A text to find in the turns."),
    ],
    "/api/dashboard/speakers": [("q", "string", False, "A part of the member name.")],
}


def summary(view):
    """The first sentence of the docstring of the page module, else of the view function."""
    mod = getattr(view, "page_module", None)
    doc = (importlib.import_module(mod).__doc__ if mod else view.__doc__) or view.__name__
    return doc.strip().split("\n")[0]


def build_spec(app):
    paths = {}
    for rule in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
        if not rule.rule.startswith("/api/") or "GET" not in rule.methods or rule.endpoint.startswith("openapi."):
            continue
        params = [{"name": arg, "in": "path", "required": True,
                   "schema": {"type": TYPES.get(type(conv).__name__, "string")}}
                  for arg, conv in rule._converters.items()]
        path = re.sub(r"<(?:[^:<>]+:)?([^<>]+)>", r"{\1}", rule.rule)
        params += [{"name": n, "in": "query", "required": req, "description": d, "schema": {"type": t}}
                   for n, t, req, d in QUERY.get(path, [])]
        group = "dashboard" if path.startswith("/api/dashboard/") else "pages" if rule.endpoint.startswith("pages.") else "other"
        paths[path] = {"get": {
            "summary": summary(app.view_functions[rule.endpoint]), "tags": [group], "parameters": params,
            "responses": {"200": {"description": "The JSON answer.", "content": {"application/json": {}}},
                          "404": {"description": "The key is unknown."}}}}
    return {"openapi": "3.0.3", "info": {"title": "Torko API", "version": "1"}, "paths": paths}


@bp.route("/api/openapi.json")
def spec():
    return jsonify(build_spec(current_app))


@bp.route("/api/docs/")
def docs():
    return send_from_directory(swagger_ui_path, "index.html")


@bp.route("/api/docs/swagger-initializer.js")
def initializer():
    js = ('window.onload = function () { window.ui = SwaggerUIBundle({ url: "/api/openapi.json", '
          'dom_id: "#swagger-ui", presets: [SwaggerUIBundle.presets.apis, SwaggerUIStandalonePreset], '
          'layout: "StandaloneLayout" }); };')
    return current_app.response_class(js, mimetype="application/javascript")


@bp.route("/api/docs/<path:name>")
def assets(name):
    return send_from_directory(swagger_ui_path, name)

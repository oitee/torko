import os
import pathlib

from flask import Flask, jsonify, request, send_from_directory

import dashboard_db
import openapi
import pages_api
import tag_search
from debate_fetch import fetch_debate, split_by_speaker, speaker_distribution
from debate_fetch_legacy import looks_legacy, split_by_speaker_legacy

# TODO: static/ is the older work-in-progress dashboard, kept for testing. Remove it when the site in web/ is complete.
app = Flask(__name__, static_folder="static", static_url_path="")

MAX_PAGE_SIZE = 100

pages_api.register()
app.register_blueprint(pages_api.bp)
app.register_blueprint(openapi.bp)


@app.route("/api/dashboard/debates")
def api_dashboard_debates():
    """The debates of the dashboard, filtered, one page at a time."""
    page = max(request.args.get("page", 1, type=int), 1)
    page_size = min(max(request.args.get("pageSize", 20, type=int), 1), MAX_PAGE_SIZE)

    result = dashboard_db.list_debates(
        date_from=request.args.get("date_from"),
        date_to=request.args.get("date_to"),
        loksabha=request.args.get("loksabha", type=int),
        session=request.args.get("session", type=int),
        parties=request.args.getlist("party"),
        speaker_codes=request.args.getlist("speaker"),
        q=(request.args.get("q") or "").strip(),
        page=page,
        page_size=page_size,
        debate_types=request.args.getlist("debate_type"),
        text_query=(request.args.get("text") or "").strip() or None,
    )

    return jsonify(
        {
            "total": result["total"],
            "page": page,
            "pageSize": page_size,
            "results": result["results"],
        }
    )


@app.route("/api/dashboard/debates/<debate_id>")
def api_dashboard_debate_detail(debate_id):
    """One debate of the dashboard, with all its turns."""
    parsed = dashboard_db.parse_composite_id(debate_id)
    if parsed is None:
        return jsonify({"error": f"Malformed debate id {debate_id!r}, expected loksabha-session-dbslno"}), 400
    detail = dashboard_db.get_debate_detail(*parsed)
    if detail is None:
        return jsonify({"error": f"No debate with id {debate_id!r}"}), 404
    return jsonify(detail)


@app.route("/api/dashboard/debates/<debate_id>/mp-diff")
def api_dashboard_debate_mp_diff(debate_id):
    """The members of the official list of one debate, compared with the members who have a turn."""
    parsed = dashboard_db.parse_composite_id(debate_id)
    if parsed is None:
        return jsonify({"error": f"Malformed debate id {debate_id!r}, expected loksabha-session-dbslno"}), 400
    diff = dashboard_db.get_mp_diff(*parsed)
    if diff is None:
        return jsonify({"error": f"No debate with id {debate_id!r}"}), 404
    return jsonify(diff)


@app.route("/api/dashboard/speakers")
def api_dashboard_speakers():
    """The members who have a turn, filtered by name."""
    q = (request.args.get("q") or "").strip()
    return jsonify({"results": dashboard_db.list_speakers(q)})


@app.route("/api/dashboard/speakers/<sansad_id>")
def api_dashboard_speaker_detail(sansad_id):
    """One member of the dashboard, with the debates in which the member has a turn."""
    detail = dashboard_db.get_speaker_detail(sansad_id)
    if detail is None:
        return jsonify({"error": f"No speaker with sansadId {sansad_id!r}"}), 404
    return jsonify(detail)


@app.route("/api/dashboard/facets")
def api_dashboard_facets():
    """The filter values of the dashboard: terms, sessions, parties, and debate types."""
    return jsonify(dashboard_db.get_facets())


_search_index = None


def search_index():
    """The tags, subjects and members for /api/search. Read once per process: they change only when the pipeline runs."""
    global _search_index
    if _search_index is None:
        with dashboard_db.get_engine().connect() as conn:
            _search_index = (*tag_search.load_index(conn), tag_search.load_members(conn))
    return _search_index


@app.route("/api/search")
def api_search():
    """The tags, places, subjects and members that match a search text."""
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"error": "q is required"}), 400
    tags, subjects, members = search_index()
    results = tag_search.search(q, tags, subjects, limit=20, members=members)
    for r in results:
        if r["kind"] in ("tag", "place"):
            r["subjects"] = [{"subject_id": s["subject_id"], "label": s["label"], "n_speeches": s["n_speeches"]}
                             for s in r["subjects"][:50]]
    return jsonify({"query": q, "results": results})


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


# The new public site: a single-page app that Vite builds into web/dist/.
# Flask sends the one file index.html for every page address, and the browser picks the page.
WEB_DIST = pathlib.Path(__file__).resolve().parent / "web" / "dist"
SITE_PAGES = ["/tag/<slug>", "/member/<int:member_id>", "/speech/<int:speech_id>", "/debate/<int:debate_id>",
              "/place/<slug>", "/search"]


def site_index(status=200):
    """index.html of the built site, with the given status. A 404 when the site is not built."""
    if not (WEB_DIST / "index.html").is_file():
        return "The site is not built. Run: cd web && npm run build", 404
    resp = send_from_directory(WEB_DIST, "index.html", max_age=0)
    resp.status_code = status
    return resp


def site_page(**_):
    return site_index()


for rule in SITE_PAGES:
    app.add_url_rule(rule, endpoint="site_" + rule.strip("/").split("/")[0], view_func=site_page)


@app.route("/assets/<path:name>")
def site_assets(name):
    """The built JavaScript and CSS. Each file name holds a hash of its content, so a browser can keep it for a year."""
    return send_from_directory(WEB_DIST / "assets", name, max_age=365 * 24 * 3600)


@app.errorhandler(404)
def not_found(error):
    """An address with no page gets the site with status 404, so that search engines do not store it.
    The site shows its own "Page not found". An API address keeps the plain 404."""
    if request.path.startswith("/api/") or not (WEB_DIST / "index.html").is_file():
        return error
    return site_index(404)


@app.route("/analysis")
def analysis():
    base = pathlib.Path(app.static_folder).parent
    template = (base / "static" / "analysis.html").read_text()
    data = (base / "fixtures" / "analysis.json").read_text()
    return template.replace("__DATA__", data, 1)


@app.route("/api/distribution")
def api_distribution():
    """One debate read live from the official site, split by speaker."""
    try:
        loksabha = int(request.args["loksabha"])
        session = int(request.args["session"])
        dbslno = int(request.args["dbslno"])
    except (KeyError, ValueError):
        return jsonify({"error": "loksabha, session, and dbslno must all be provided as integers"}), 400

    try:
        data = fetch_debate(loksabha, session, dbslno)
    except Exception as exc:  # sansad.in errors, timeouts, etc.
        return jsonify({"error": f"Failed to fetch debate: {exc}"}), 502

    html = data.get("debateDesc", "")
    if not html:
        return jsonify({"error": "No transcript (debateDesc) found for this debate item."}), 404

    mp_part_detail_list = data.get("mpPartDetailList", [])
    legacy = looks_legacy(html)
    from db_roster import load_db_roster

    db_roster = load_db_roster(loksabha)
    segments = (
        split_by_speaker_legacy(html, mp_part_detail_list, db_roster)
        if legacy
        else split_by_speaker(html, mp_part_detail_list, db_roster)
    )
    dist = speaker_distribution(segments)

    return jsonify(
        {
            "debateDate": data.get("debateDate"),
            "debateType": data.get("debateType"),
            "format": "legacy" if legacy else "modern",
            "totalSegments": len(segments),
            "distribution": dist,
            "segments": segments,
        }
    )


if __name__ == "__main__":
    # FLASK_DEBUG=false turns off the debug mode. The default is true, for local work.
    app.run(debug=os.environ.get("FLASK_DEBUG", "true").lower() == "true", port=5050)

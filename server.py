from flask import Flask, jsonify, request, send_from_directory

import dashboard_db
import openapi
import pages_api
import tag_search
from debate_fetch import fetch_debate, split_by_speaker, speaker_distribution
from debate_fetch_legacy import looks_legacy, split_by_speaker_legacy

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
    """The tags and subjects for /api/search. Read once per process: they change only when the pipeline runs."""
    global _search_index
    if _search_index is None:
        with dashboard_db.get_engine().connect() as conn:
            _search_index = tag_search.load_index(conn)
    return _search_index


@app.route("/api/search")
def api_search():
    """The tags and subjects that match a search text."""
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"error": "q is required"}), 400
    tags, subjects = search_index()
    results = tag_search.search(q, tags, subjects, limit=20)
    for r in results:
        if r["kind"] == "tag":
            r["subjects"] = [{"subject_id": s["subject_id"], "label": s["label"], "n_speeches": s["n_speeches"]}
                             for s in r["subjects"][:50]]
    return jsonify({"query": q, "results": results})


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/analysis")
def analysis():
    import pathlib

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
    app.run(debug=True, port=5050)

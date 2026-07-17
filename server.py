"""
Step 3: tiny local web app around debate_fetch.py.

Serves a single HTML page (static/index.html) that lets the user enter a
Lok Sabha number, session number, and debate serial number, then calls
sansad.in via /api/distribution and renders the speaker-wise distribution.

Also serves /api/dashboard/* — the debate-dashboard demo. Contract and
rationale: internal_docs/026_DASHBOARD_DEMO.md, internal_docs/028_TURNS_TABLE.md.
Backed by the `turns` table (dashboard_db.py) — real corpus, not the frozen
fixture the routes used before `turns` existed. FE (static/dashboard.html,
debate.html, speaker.html) is unchanged: same JSON contract either way.

Run: source .venv/bin/activate && python3 server.py
"""
from flask import Flask, jsonify, request, send_from_directory

import dashboard_db
from debate_fetch import fetch_debate, split_by_speaker, speaker_distribution
from debate_fetch_legacy import looks_legacy, split_by_speaker_legacy

app = Flask(__name__, static_folder="static", static_url_path="")


@app.route("/api/dashboard/debates")
def api_dashboard_debates():
    page = max(request.args.get("page", 1, type=int), 1)
    page_size = max(request.args.get("pageSize", 20, type=int), 1)

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
    parsed = dashboard_db.parse_composite_id(debate_id)
    if parsed is None:
        return jsonify({"error": f"Malformed debate id {debate_id!r}, expected loksabha-session-dbslno"}), 400
    detail = dashboard_db.get_debate_detail(*parsed)
    if detail is None:
        return jsonify({"error": f"No debate with id {debate_id!r}"}), 404
    return jsonify(detail)


@app.route("/api/dashboard/debates/<debate_id>/mp-diff")
def api_dashboard_debate_mp_diff(debate_id):
    parsed = dashboard_db.parse_composite_id(debate_id)
    if parsed is None:
        return jsonify({"error": f"Malformed debate id {debate_id!r}, expected loksabha-session-dbslno"}), 400
    diff = dashboard_db.get_mp_diff(*parsed)
    if diff is None:
        return jsonify({"error": f"No debate with id {debate_id!r}"}), 404
    return jsonify(diff)


@app.route("/api/dashboard/speakers")
def api_dashboard_speakers():
    q = (request.args.get("q") or "").strip()
    return jsonify({"results": dashboard_db.list_speakers(q)})


@app.route("/api/dashboard/speakers/<sansad_id>")
def api_dashboard_speaker_detail(sansad_id):
    detail = dashboard_db.get_speaker_detail(sansad_id)
    if detail is None:
        return jsonify({"error": f"No speaker with sansadId {sansad_id!r}"}), 404
    return jsonify(detail)


@app.route("/api/dashboard/facets")
def api_dashboard_facets():
    return jsonify(dashboard_db.get_facets())


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api/distribution")
def api_distribution():
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

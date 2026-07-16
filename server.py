"""
Step 3: tiny local web app around debate_fetch.py.

Serves a single HTML page (static/index.html) that lets the user enter a
Lok Sabha number, session number, and debate serial number, then calls
sansad.in via /api/distribution and renders the speaker-wise distribution.

Run: source .venv/bin/activate && python3 server.py
"""
from flask import Flask, jsonify, request, send_from_directory

from debate_fetch import fetch_debate, split_by_speaker, speaker_distribution
from debate_fetch_legacy import looks_legacy, split_by_speaker_legacy

app = Flask(__name__, static_folder="static", static_url_path="")


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

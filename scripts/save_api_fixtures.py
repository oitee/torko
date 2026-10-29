"""Save the API answers that the Home page and the Method page read, as JSON files for the site tests.

The tests of the site run with no server and no database. They read these files instead.
Run it again when the shape of an API answer changes. It calls the Flask app directly, so no server must run.

    source .venv/bin/activate && set -a && source .env && set +a
    python3 scripts/save_api_fixtures.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from server import app

OUT = Path(__file__).resolve().parent.parent / "web" / "tests" / "fixtures"

CALLS = {
    "home/home.json": "/api/home",
    "home/home_featured.json": "/api/home/featured",
    "method/method.json": "/api/method",
}


def main() -> None:
    client = app.test_client()
    for name, url in CALLS.items():
        (OUT / name).parent.mkdir(parents=True, exist_ok=True)
        resp = client.get(url)
        if resp.status_code != 200:
            sys.exit(f"{url} answered {resp.status_code}")
        (OUT / name).write_text(json.dumps(resp.get_json(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"{name}  {url}")


if __name__ == "__main__":
    main()

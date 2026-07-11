# Parliament Debates parser 🏛️

> **⚠️ Work in progress.** The project is currently in an exploratory phase - trying out different permutations to see what can be achieved out of parliamentary debates

Fetches a Lok Sabha debate transcript from the [sansad.in](https://sansad.in)
API, cleans the messy Word-export HTML into readable text, splits it into
per-speaker turns ("who said what"), and matches each speaker to the official
MP roster. There's a tiny web app that shows a speaker-wise word/intervention
distribution for any debate.

Two eras of transcript are handled:

- **Modern** (newer Lok Sabhas) — [`debate_fetch.py`](debate_fetch.py)
- **Legacy** (~pre-2004, e.g. LS 13 / 1999) — [`debate_fetch_legacy.py`](debate_fetch_legacy.py)

The app auto-detects which one a debate needs. How it all works, in plain
language, is documented in [`PARSING_STRATEGY.md`](PARSING_STRATEGY.md); API
details are in [`SANSAD_API_FINDINGS.md`](SANSAD_API_FINDINGS.md).

---

## Setup

Requires Python 3.10+.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

### The web app

```bash
source .venv/bin/activate
python3 server.py
```

Then open <http://localhost:5050> and enter a Lok Sabha number, session number,
and debate serial number (`dbSlNo`).

### From the command line

Parse a single debate and print its speaker breakdown:

```bash
# modern debates
python3 debate_fetch.py --loksabha 18 --session 3 --dbslno 1758

# legacy debates (older format)
python3 debate_fetch_legacy.py --loksabha 13 --session 14 --dbslno 7793
```

Add `--summary-only` to skip the per-turn previews.

## Tests

The parser has an extensive offline unit-test suite (no network needed):

```bash
source .venv/bin/activate
python3 -m pytest
```

An overview of *what kinds* of cases are covered — one representative
input→output per parsing strategy — is in [`TEST_CASES.md`](TEST_CASES.md).

---

## Status / known gaps

This is early and being iterated on. The bigger known limitations:

- **Hindi/Urdu names don't match the romanised roster** yet (needs
  transliteration), so many Indic-script turns stay `unresolved`.
- **The presiding officer** (`MR. SPEAKER`, `MR. CHAIRMAN`, …) isn't in the MP
  roster, so those turns are `unresolved`.
- **Legacy-font Hindi** in old transcripts is split into the right turns but its
  text is still mojibake (needs a decode pass).

The full list lives at the bottom of [`PARSING_STRATEGY.md`](PARSING_STRATEGY.md).

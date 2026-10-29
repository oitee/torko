# Saved API answers for the Home page

Each file is one answer of the Torko API, saved from the real database. The site tests read these files, so the tests need no server and no database.

| File | API address | Use on the Home page |
|---|---|---|
| `home.json` | `/api/home` | The site figures (`corpus`: debates, members, tags, terms, first and last date, error rate), the newest session, its typical subjects, and the chamber. |
| `home_featured.json` | `/api/home/featured` | The hand-checked sample: one member (with the seat and the state), one quote (with the tags of its speech), one trend, and the search ideas. |

Each answer holds a `counts_note` or a `note` that says what each count is counted over.

To save the files again, run `python3 scripts/save_api_fixtures.py` from the repository root. It needs the local database.

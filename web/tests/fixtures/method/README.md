# Saved API answer for the Method page

| File | API address | Use on the Method page |
|---|---|---|
| `method.json` | `/api/method` | The figures of each step (`turns`, `speeches`, `corpus`), the printed labels of one member (`example`), and the share of the source text that Torko does not read (`unread_text`). |

The `counts_note` of the answer says what each count is counted over.

To save the file again, run `python3 scripts/save_api_fixtures.py` from the repository root. It needs the local database.

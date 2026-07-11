# Parser test cases — the archetypes we cover

This is a map of **what kinds of things the tests check**, not a line-by-line
listing of all 70 tests. For each parsing strategy there is one representative
"archetype" with a concrete **input → expected output**. The full assertions
live in [`tests/`](tests/); the strategies themselves are explained in
[`PARSING_STRATEGY.md`](PARSING_STRATEGY.md).

Run them with:

```bash
.venv/bin/python -m pytest        # 70 tests, ~0.1s, no network
```

The suite is organised the same way the parser is — Part 1 (clean text),
Part 2 (split modern), Part 3 (match names), Part 4 (legacy format).

---

## Part 1 — Cleaning text  ·  [`tests/test_clean_text.py`](tests/test_clean_text.py)

| Archetype | Function | Input | Expected output |
|---|---|---|---|
| Collapse whitespace runs | `_clean_inline` | `"Thank    you,\n   Chairman"` | `"Thank you, Chairman"` |
| Non-breaking space (`&nbsp;`/`\xa0`) → space | `_clean_inline` | `"Constitution.\xa0\xa0\xa0 I am"` | `"Constitution. I am"` |
| Space before ASCII punctuation removed | `_clean_inline` | `"Sir , I agree ."` | `"Sir, I agree."` |
| Space before Devanagari *danda* removed | `_clean_inline` | `"बैठे हैं ।"` | `"बैठे हैं।"` |
| Real paragraph break (`</p>`) preserved | `html_to_clean_text` | `"<p>First</p><p>Second</p>"` | `"First\n\nSecond"` |
| `<br>` counts as a real break | `html_to_clean_text` | `"<p>line a<br>line b</p>"` | `"line a\n\nline b"` |
| Fake mid-paragraph wrap collapsed to a space | `html_to_clean_text` | `"<p>Chairman Sir\nfor giving</p>"` | `"Chairman Sir for giving"` |
| Empty paragraphs dropped | `html_to_clean_text` | `"<p>real</p><p>  </p><p>text</p>"` | `"real\n\ntext"` |

---

## Part 2 — Splitting into turns (modern)  ·  [`tests/test_split_modern.py`](tests/test_split_modern.py)

| Archetype | Function | Input | Expected output |
|---|---|---|---|
| Bold label found past an empty anchor-wrapping bold | `_leading_bold` | `<b><a name="344*24"></a></b><b>SHRI X:</b> hi` | `"SHRI X:"` |
| Bold not at paragraph start → not a label | `_leading_bold` | `"intro text <b>SHRI X:</b>"` | `""` |
| Bold label ending in colon detected | `_label_colon_pos` | `<b>SHRI X (PLACE):</b> …` | index of the `:` |
| Mid-sentence colon in plain text ignored | `_label_colon_pos` | `"the ratio was 3:1"` | `None` |
| Colon past the 200-char window ignored | `_label_colon_pos` | `<b>{250×"A"}: tail</b>` | `None` |
| Read anchor id `code*part` | `_anchor_id` | `<a name="344*24">` | `("344", "24")` |
| Anchored turn → canonical name + part | `split_by_speaker` | `<a name="344*24">SHRI A. RAJA:` Hello. | `mpName="Shri Raja A"`, `nameSource="anchor"` |
| Following non-label paragraph glued on | `split_by_speaker` | label para + `<p>Second para.</p>` | one turn, text `"First…\n\nSecond para."` |
| Anchor-less bold label opens its own turn | `split_by_speaker` | two bold labels, 2nd has no anchor | 2 turns; 2nd resolved by name |
| Star prefix stripped from label | `split_by_speaker` | `<b>*57 SHRI …:</b>` | `speakerLabel` without `*57` |
| Text before the first speaker is unattributed | `split_by_speaker` | `<p>11.00 hrs…</p>` then a label | leading turn with `speakerLabel=None` |
| Aggregate words/interventions per speaker | `speaker_distribution` | two turns same `mpCode` | `interventions=2`, summed `words` |
| Distribution sorted by word count desc | `speaker_distribution` | long turn + short turn | longer speaker first |
| Unresolved label keeps its own bucket | `speaker_distribution` | preamble + `MR. SPEAKER` | separate `(unattributed)` and `MR. SPEAKER` rows |

---

## Part 3 — Matching names to the roster  ·  [`tests/test_normalize_resolve.py`](tests/test_normalize_resolve.py)

### Normalisation (`_normalize_name`)

| Archetype | Input | Expected output |
|---|---|---|
| Drop honorific + constituency | `"SHRI A. RAJA (NILGIRIS)"` | `["a", "raja"]` |
| Ministerial title → name inside parens | `"THE MINISTER OF STEEL (SHRI PRALHAD JOSHI)"` | `["pralhad", "joshi"]` |
| **Honorific-only parenthetical is NOT the name** (fix 2) | `"Dr. (Smt.) V. Saroja"` | `["v", "saroja"]` |
| Purely-honorific label collapses to empty | `"Dr."` | `[]` |
| Indic script passes through (won't match roster) | `"श्री किरेन रिजिजू"` | non-empty, non-ASCII tokens |

### Four-tier matching (`resolve_speaker`)

| Archetype (tier) | Input label vs roster | Expected `nameSource` |
|---|---|---|
| Tier 1 — exact | `"SHRI KODIKUNNIL SURESH"` vs `Shri Kodikunnil Suresh` | `name-exact` |
| Tier 2 — order-insensitive | `"SHRI A. RAJA"` vs `Shri Raja A` | `name-join` |
| Tier 2 — spacing-insensitive | `"…SRIKRISHNA…"` vs `…Sri Krishna…` | `name-join` |
| Tier 3 — unique subset | `"SHRI SURESH KODIKUNNIL EXTRA"` | `name-partial` |
| No match | `"MR. SPEAKER"` (not in roster) | `(None, None)` |
| **Empty-token roster entry never wildcard-matches** (fix 1) | any label vs a roster of only `"Dr."` | `(None, None)` |
| Ambiguous subset rejected | `"SHRI KUMAR"` vs two different `… Kumar` | `(None, None)` |

### Writing results back (`annotate_speakers`)

| Archetype | Input segment | Expected |
|---|---|---|
| Anchored turn | has `mpCode` | `nameSource="anchor"`, untouched |
| Anchor-less match inherits official id + name | label `SHRI KODIKUNNIL SURESH` | `mpCode="100"`, canonical name, `name-exact` |
| No match keeps raw label | label `MR. SPEAKER` | `nameSource="unresolved"`, label kept |
| Segment with no label | `speakerLabel=None` | `nameSource=None` |
| **Saroja regression, end to end** (fix 1) | `SHRI BIKRAM KESHARI DEO (KALAHANDI)` + Saroja in roster | stays `unresolved`, **not** relabelled Saroja |

---

## Part 4 — Legacy format  ·  [`tests/test_split_legacy.py`](tests/test_split_legacy.py)

| Archetype | Function | Input | Expected output |
|---|---|---|---|
| Modern anchor → not legacy | `looks_legacy` | `<A name="3972*1">` | `False` |
| Part-less anchor → legacy | `looks_legacy` | `<A name="209">` | `True` |
| Self-close the unclosed anchor | `_sanitize_legacy_html` | `<A name="209">text` | `<A name="209"/>text` |
| ALL-CAPS name is a label | `_is_caps_label` | `"SHRI RUPCHAND PAL (HOOGHLY)"` | `True` |
| Lowercase sentence is not a label | `_is_caps_label` | `"Sir, I want to oppose"` | `False` |
| Digits/punctuation only is not a label | `_is_caps_label` | `"11.09 hrs"` | `False` |
| Caps-colon opens a turn | `_label_colon_pos` | `"MR. SPEAKER: Motion moved."` | index of `:` |
| Read part-less anchor id | `_anchor_id` | `<a name="209">` | `"209"` |
| Caps label opens a turn | `split_by_speaker_legacy` | `"MR. SPEAKER: Motion moved."` | 1 turn, body `"Motion moved."` |
| Lowercase line is a continuation | `split_by_speaker_legacy` | caps turn + lowercase line | 1 turn, both lines joined |
| Pending anchor on empty `<p>` attaches to next block | `split_by_speaker_legacy` | `<p><A name="209"></p>` then speech | turn carries `mpCode="209"` |
| `<h6>` blocks are walked too | `split_by_speaker_legacy` | `<p>SHRI A: …<h6>SHRI B: …</h6>` | 2 turns (A and B) |
| Bold `Title:` header skipped | `split_by_speaker_legacy` | `<b>Title:</b> …` + a real turn | only the real turn |
| Star prefix stripped in caps label | `split_by_speaker_legacy` | `"*57 SHRI N. K. PREMACHANDRAN …:"` | label without `*57` |

---

## The two regression cases (why this suite exists)

Both guard the bug where **entry 11 of LS 13 / Session 14 / dbSlNo 7793**
(`SHRI BIKRAM KESHARI DEO`) was mis-attributed to `Dr. (Smt.) V. Saroja`:

1. **Fix 1 — empty-token wildcard guard** (`resolve_speaker`): a roster name that
   normalises to `[]` used to be a subset of *every* label, so it matched
   everything. Test:
   `TestResolveSpeaker::test_empty_token_roster_entry_never_wildcard_matches`.
2. **Fix 2 — honorific-only parenthetical** (`_normalize_name`): `"(Smt.)"` was
   wrongly read as a ministerial name, collapsing `Dr. (Smt.) V. Saroja` to `[]`
   in the first place. Test:
   `TestNormalizeName::test_honorific_only_parenthetical_is_not_treated_as_the_name`.

The end-to-end guard is
`TestAnnotateSpeakers::test_saroja_regression_end_to_end`.

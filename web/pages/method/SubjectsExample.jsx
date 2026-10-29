import React from "react";
import { Link } from "react-router-dom";
import { formatDateISO } from "../../assets/js/format.js";
import "./MethodExample.css";
import "./SubjectsExample.css";

// Split text into parts, and mark each place where a mention of a subject occurs.
// A match ignores case. The first mention in the text wins where two overlap.
export function markMentions(text, mentions) {
  const source = text || "";
  const lower = source.toLowerCase();
  const ranges = [];
  for (const m of mentions) {
    const needle = (m.mention || "").trim().toLowerCase();
    if (needle.length < 3) continue;
    const at = lower.indexOf(needle);
    if (at < 0) continue;
    const end = at + needle.length;
    if (ranges.some((r) => at < r.end && end > r.start)) continue;
    ranges.push({ start: at, end, kept: m.kept });
  }
  ranges.sort((a, b) => a.start - b.start);
  const parts = [];
  let pos = 0;
  for (const r of ranges) {
    if (r.start > pos) parts.push({ text: source.slice(pos, r.start) });
    parts.push({ text: source.slice(r.start, r.end), mark: true, kept: r.kept });
    pos = r.end;
  }
  if (pos < source.length) parts.push({ text: source.slice(pos) });
  return parts;
}

// SubjectsExample shows one short speech with its subjects marked in the text, the TLDR,
// and each subject that the model named, with the result of the check.
// The example comes from /api/method → examples.subjects.
export default function SubjectsExample({ example }) {
  const items = Array.isArray(example?.items) ? example.items : [];
  if (!example?.text || items.length === 0) return null;

  const parts = markMentions(example.text, items);

  return (
    <div className="subjects-example">
      <div className="method-box">
        <p className="method-box__label">
          The speech ·{" "}
          {example.member_id ? <Link to={`/member/${example.member_id}`}>{example.member}</Link> : example.member}
          {example.date && (
            <>
              {" "}
              · <span className="method-source__date">{formatDateISO(example.date)}</span>
            </>
          )}
        </p>
        <p className="subjects-example__text">
          {parts.map((p, i) =>
            p.mark ? (
              <mark key={i} className={p.kept ? "subjects-example__mark" : "subjects-example__mark subjects-example__mark--dropped"}>
                {p.text}
              </mark>
            ) : (
              <React.Fragment key={i}>{p.text}</React.Fragment>
            )
          )}
        </p>
      </div>
      <div className="method-arrow" aria-hidden="true">
        ↓
      </div>
      <div className="method-box method-after">
        {example.summary && (
          <div className="subjects-example__tldr">
            <p className="subjects-example__tldr-label">TLDR</p>
            <p className="subjects-example__tldr-text">{example.summary}</p>
          </div>
        )}
        <p className="method-box__label">Subjects that the model named, and the result of the check</p>
        <ul className="subjects-example__items">
          {items.map((it, i) => (
            <li key={`${it.name}-${i}`} className={it.kept ? "subjects-example__item" : "subjects-example__item subjects-example__item--dropped"}>
              <span className="subjects-example__verdict" aria-hidden="true">
                {it.kept ? "✓" : "✕"}
              </span>
              <span className="subjects-example__name">{it.name}</span>
              <span className="subjects-example__state">{it.kept ? "kept" : "dropped"}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

export { SubjectsExample };

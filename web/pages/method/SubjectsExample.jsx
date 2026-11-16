import React, { useState } from "react";
import { Link } from "react-router-dom";
import { formatDateISO } from "../../assets/js/format.js";
import useDemo from "./useDemo.js";
import "./MethodExample.css";
import "./SubjectsExample.css";

// Split text into parts, and mark each place where a mention of a subject occurs.
// A match ignores case. The first mention in the text wins where two overlap.
export function markMentions(text, mentions) {
  const source = text || "";
  const lower = source.toLowerCase();
  const ranges = [];
  for (const [item, m] of mentions.entries()) {
    const needle = (m.mention || "").trim().toLowerCase();
    if (needle.length < 3) continue;
    const at = lower.indexOf(needle);
    if (at < 0) continue;
    const end = at + needle.length;
    if (ranges.some((r) => at < r.end && end > r.start)) continue;
    ranges.push({ start: at, end, kept: m.kept, item });
  }
  ranges.sort((a, b) => a.start - b.start);
  const parts = [];
  let pos = 0;
  for (const r of ranges) {
    if (r.start > pos) parts.push({ text: source.slice(pos, r.start) });
    parts.push({ text: source.slice(r.start, r.end), mark: true, kept: r.kept, item: r.item });
    pos = r.end;
  }
  if (pos < source.length) parts.push({ text: source.slice(pos) });
  return parts;
}

// SubjectsExample shows one short speech with its subjects marked in the text, the TLDR,
// and each subject that the model named, with the result of the check.
// While the example is on screen, the subjects in the speech get their underlines one at a time, in reading order.
// Then the TLDR types itself out. Then the label of the chips and each subject chip appear.
// Each chip then shows the result of the check. A dropped subject turns red in the speech at the same time as its chip.
// The final state holds for six seconds. The demo runs again and again.
// The example comes from /api/method → examples.subjects.
export default function SubjectsExample({ example }) {
  const items = Array.isArray(example?.items) ? example.items : [];
  const summary = example?.summary || "";
  const [typed, setTyped] = useState(null);
  // The first render shows the final state, so the example is complete before the demo starts, or without it.
  const [read, setRead] = useState(Infinity);
  const [shown, setShown] = useState(items.length);
  const [judged, setJudged] = useState(items.length);

  const [ref, isStatic] = useDemo(async (sleep) => {
    setTyped("");
    setRead(0);
    setShown(0);
    setJudged(0);
    await sleep(400);
    const nMarks = markMentions(example.text, items).filter((p) => p.mark).length;
    for (let k = 1; k <= nMarks; k++) {
      setRead(k);
      await sleep(350);
    }
    await sleep(300);
    for (let i = 1; i <= summary.length; i++) {
      setTyped(summary.slice(0, i));
      await sleep(18);
    }
    await sleep(400);
    for (let k = 1; k <= items.length; k++) {
      setShown(k);
      await sleep(150);
    }
    await sleep(500);
    for (let k = 1; k <= items.length; k++) {
      setJudged(k);
      await sleep(180);
    }
    await sleep(6000);
  }, 600);

  if (!example?.text || items.length === 0) return null;

  const parts = markMentions(example.text, items);
  const tldr = isStatic || typed == null ? summary : typed;
  const nRead = isStatic ? Infinity : read;
  const nShown = isStatic ? items.length : shown;
  const nJudged = isStatic ? items.length : judged;
  let markIndex = 0;

  return (
    <div ref={ref} className="method-demo subjects-example">
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
            <mark
              key={i}
              className={[
                "subjects-example__mark",
                // A dropped mention turns red only when its chip shows the result of the check.
                !p.kept && p.item < nJudged ? "subjects-example__mark--dropped" : "",
                markIndex++ < nRead ? "is-read" : "",
              ].join(" ").trim()}
            >
              {p.text}
            </mark>
          ) : (
            <React.Fragment key={i}>{p.text}</React.Fragment>
          )
        )}
      </p>
      {summary && (
        <p className="subjects-example__tldr">
          <b className="subjects-example__tldr-label">TLDR</b>
          {tldr === summary ? <span>{summary}</span> : <span aria-label={summary}>{tldr}</span>}
        </p>
      )}
      <p className={nShown > 0 ? "method-box__label subjects-example__label" : "method-box__label subjects-example__label is-hidden"}>Subjects that the model named, and the result of the check</p>
      <ul className="subjects-example__items">
        {items.map((it, i) => {
          const cls = ["subjects-example__item"];
          if (i < nShown) cls.push("is-in");
          if (i < nJudged) cls.push(it.kept ? "is-kept" : "is-dropped");
          return (
            <li key={`${it.name}-${i}`} className={cls.join(" ")}>
              <span className="subjects-example__name">{it.name}</span>
              <span className="method-sr">{it.kept ? "kept" : "dropped"}</span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

export { SubjectsExample };

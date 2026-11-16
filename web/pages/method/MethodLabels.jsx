import React, { useState } from "react";
import { Link } from "react-router-dom";
import { formatNumber, scriptLang } from "../../assets/js/format.js";
import useDemo from "./useDemo.js";
import "./MethodExample.css";
import "./MethodLabels.css";

// MethodLabels shows the most frequent printed names of one member, with the number of turns under each.
// While the example is on screen, each printed name appears large and changes from the previous name,
// one character at a time. Changed characters show in green. A list grows below.
// The names show grouped by script: Hindi first, then Urdu, then English. Inside a group, the order stays by turns.
// When the script changes, the stage clears, and the new name types in from empty, all in green.
// A change from one script to another one character at a time shows mixed-script text that means nothing.
// After the last name, lines join every name into the one member.
// The example comes from /api/method → example.

// The diagram where all printed names join into the member. It is the final state of the demo.
function Converge({ labels, name }) {
  const H = labels.length * 24 + 16;
  const mid = H / 2;
  const words = name.split(" ");
  const half = Math.ceil(words.length / 2);
  const lines = words.length > 1 ? [words.slice(0, half).join(" "), words.slice(half).join(" ")] : [name];
  return (
    <svg viewBox={`0 0 640 ${H}`} role="img" aria-label={`${labels.length} printed names join into one member, ${name}.`}>
      {labels.map((r, i) => {
        const y = 20 + i * 24;
        const hi = scriptLang(r.label) === "hi";
        return (
          <g key={r.label}>
            <path
              className="method-labels__line"
              style={{ animationDelay: `${i * 0.08}s` }}
              d={`M358 ${y - 4} C 430 ${y - 4}, 440 ${mid}, 500 ${mid}`}
            />
            <text className={hi ? "is-hi" : undefined} x="8" y={y} lang={scriptLang(r.label)}>
              {r.label}
            </text>
            <text className="method-labels__cnt" textAnchor="end" x="350" y={y}>
              {formatNumber(r.n)}
            </text>
          </g>
        );
      })}
      <rect className="method-labels__node" x="500" y={mid - 22} width="132" height="44" />
      {lines.map((l, i) => (
        <text
          key={l}
          className="method-labels__nodelbl"
          x="566"
          y={lines.length === 1 ? mid + 5 : mid - 3 + i * 16}
          textAnchor="middle"
        >
          {l}
        </text>
      ))}
    </svg>
  );
}

const SCRIPT_RANK = { hi: 0, ur: 1 };

// The form of a printed name: 0 the name only, 1 the name with the constituency in brackets,
// 2 the name with the constituency and the state in brackets, for example "(BERHAMPORE, WEST BENGAL)".
function nameForm(label) {
  const m = label.match(/\(([^)]*)\)/);
  if (!m) return 0;
  return m[1].includes(",") ? 2 : 1;
}

// demoOrder gives the labels grouped by script: Hindi, then Urdu, then English.
// Inside each script, the names go by form: the name only, then with the constituency, then with the state too.
// Each step then adds one part to the name. The sort is stable, so names of one form keep the order of the answer.
function demoOrder(labels) {
  const rank = (r) => SCRIPT_RANK[scriptLang(r.label)] ?? 2;
  return labels
    .map((r, i) => [r, i])
    .sort((a, b) => rank(a[0]) - rank(b[0]) || nameForm(a[0].label) - nameForm(b[0].label) || a[1] - b[1])
    .map(([r]) => r);
}

const VIRAMA = "्";
const segmenter = typeof Intl !== "undefined" && Intl.Segmenter ? new Intl.Segmenter("hi", { granularity: "grapheme" }) : null;

// letters cuts a name into the units that the demo types one at a time.
// A unit is one written letter with its marks, not one code point. In Hindi, "री" is two code points (र and ी).
// A unit that ends with a virama (्) joins the next unit, so a joined letter such as "श्री" stays whole.
// Safari does not join a mark to its letter across two elements, so a mark alone shows on a dotted circle.
function letters(text) {
  const parts = segmenter ? Array.from(segmenter.segment(text), (s) => s.segment) : Array.from(text);
  const out = [];
  for (const p of parts) {
    const last = out.length - 1;
    if (last >= 0 && (out[last].endsWith(VIRAMA) || /^[ऀ-ःऺ-ॏ॑-ॗॢॣ]/.test(p))) {
      out[last] += p;
    } else {
      out.push(p);
    }
  }
  return out;
}

function Stage({ stage }) {
  if (!stage) return <div className="method-labels__stage" />;
  const { prev, target, upto, count } = stage;
  const n = Math.max(prev.length, target.length);
  // Join the letters of one colour into one span, so the browser shapes each word as one text.
  const runs = [];
  for (let i = 0; i < n; i++) {
    const c = i < upto ? target[i] : prev[i];
    if (c == null) continue;
    const diff = i < upto && prev[i] !== target[i];
    const last = runs[runs.length - 1];
    if (last && last.diff === diff) last.text += c;
    else runs.push({ diff, text: c });
  }
  const out = runs.map((r, i) => (
    <span key={i} className={r.diff ? "method-labels__ch is-diff" : "method-labels__ch"}>
      {r.text}
    </span>
  ));
  const hi = scriptLang(target.join("")) === "hi";
  return (
    <div className={hi ? "method-labels__stage is-hi" : "method-labels__stage"} aria-hidden="true">
      {out}
      {upto >= n && <span className="method-labels__stagecnt">{formatNumber(count)}</span>}
    </div>
  );
}

export default function MethodLabels({ example }) {
  const labels = demoOrder(Array.isArray(example?.labels) ? example.labels : []);
  const [stage, setStage] = useState(null);
  const [rows, setRows] = useState(0);
  const [joined, setJoined] = useState(false);

  const [ref, isStatic] = useDemo(async (sleep) => {
    setJoined(false);
    setRows(0);
    setStage(null);
    let prev = [];
    for (let k = 0; k < labels.length; k++) {
      const target = letters(labels[k].label);
      const count = labels[k].n;
      if (k > 0 && scriptLang(labels[k].label) !== scriptLang(labels[k - 1].label)) {
        prev = [];
        setStage(null);
        await sleep(300);
      }
      const n = Math.max(prev.length, target.length);
      setStage({ prev, target, upto: 0, count });
      await sleep(300);
      for (let i = 1; i <= n; i++) {
        if (prev[i - 1] !== target[i - 1]) {
          setStage({ prev, target, upto: i, count });
          await sleep(45);
        }
      }
      setStage({ prev, target, upto: n, count });
      await sleep(700);
      setRows(k + 1);
      prev = target;
      await sleep(400);
    }
    await sleep(800);
    setJoined(true);
    await sleep(4000);
  }, 1500);

  if (labels.length === 0) return null;
  const showJoined = isStatic || joined;

  return (
    <figure ref={ref} className="method-demo method-labels">
      <figcaption className="method-box__label">
        The {labels.length} most frequent printed names of one member:{" "}
        <Link to={`/member/${example.member_id}`}>{example.name}</Link>
      </figcaption>
      {showJoined ? (
        <Converge labels={labels} name={example.name} />
      ) : (
        <div className="method-labels__grow">
          <Stage stage={stage} />
          <ul className="method-labels__list" aria-hidden="true">
            {labels.slice(0, rows).map((r) => (
              <li key={r.label} className={scriptLang(r.label) === "hi" ? "is-hi" : undefined}>
                <span>{r.label}</span>
                <span>{formatNumber(r.n)}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </figure>
  );
}

export { MethodLabels, Stage, demoOrder, letters };

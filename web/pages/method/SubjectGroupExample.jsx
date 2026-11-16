import React, { useState } from "react";
import { Link } from "react-router-dom";
import { formatNumber } from "../../assets/js/format.js";
import useDemo from "./useDemo.js";
import "./MethodExample.css";
import "./SubjectGroupExample.css";

const MAX_NAMES = 3;

// Cut a long name so that it fits in its box of the diagram.
function fit(s, max) {
  return s.length > max ? `${s.slice(0, max - 1)}…` : s;
}

// SubjectGroupExample shows how different names of one subject join into one specific subject, and how
// that subject links to a broad tag. Lines draw from the names to the subject, then from the subject to the tag.
// While the example is on screen, the diagram draws itself again and again.
// The example comes from /api/method → examples.subject_group.
export default function SubjectGroupExample({ example }) {
  const all = Array.isArray(example?.names) ? example.names : [];
  const [pass, setPass] = useState(0);
  const [ref] = useDemo(async (sleep) => {
    setPass((p) => p + 1);
    await sleep(5500);
  }, 0);

  if (!example?.label || all.length === 0) return null;

  const names = all.slice(0, MAX_NAMES);
  const total = Math.max(example.n_names || 0, all.length);
  const rowY = (i) => 14 + i * 46;
  const mid = (rowY(0) + rowY(names.length - 1) + 26) / 2;
  const H = Math.max(rowY(names.length - 1) + 26 + 14, mid + 40);
  const hasTag = Boolean(example.tag);
  const W = hasTag ? 640 : 460;
  const subjText = `${fit(example.label, 26)}`;
  const label = `${names.length} names join into the subject ${example.label}${hasTag ? `, which links to the tag ${example.tag}` : ""}.`;

  return (
    <div ref={ref} className="method-demo group-example">
      <p className="method-box__label">
        Names in different speeches{total > names.length ? ` · ${names.length} of ${formatNumber(total)}` : ""}
      </p>
      <svg key={pass} viewBox={`0 0 ${W} ${H}`} role="img" aria-label={label}>
        {names.map((n, i) => (
          <g key={n}>
            <rect className="group-example__box" x="8" y={rowY(i)} width="210" height="26" />
            <text className="group-example__t is-sm" x="18" y={rowY(i) + 17}>
              “{fit(n, 30)}”
            </text>
            <path className="group-example__edge" d={`M218 ${rowY(i) + 13} C 250 ${rowY(i) + 13}, 250 ${mid}, 280 ${mid}`} />
          </g>
        ))}
        <g className="group-example__fade is-d1">
          <rect className="group-example__box is-subj" x="280" y={mid - 15} width="176" height="30" />
          <text className="group-example__t" x="290" y={mid + 4}>
            {subjText}
          </text>
          {example.speeches != null && (
            <text className="group-example__t is-sm is-meta" x="290" y={mid + 32}>
              {formatNumber(example.speeches)} speeches
            </text>
          )}
        </g>
        {hasTag && (
          <>
            <path className="group-example__edge is-late" d={`M456 ${mid} L 500 ${mid}`} />
            <g className="group-example__fade is-d2">
              <rect className="group-example__box is-tag" x="500" y={mid - 16} width="130" height="32" />
              <text className="group-example__t is-bold" x="510" y={mid + 4}>
                {fit(example.tag, 16)}
              </text>
            </g>
          </>
        )}
      </svg>
      <p className="method-source">
        One specific subject: {example.label}
        {example.speeches != null && <> · {formatNumber(example.speeches)} speeches</>}
        {hasTag && (
          <>
            {" "}
            · Under the tag <Link to={`/tag/${example.tag_slug}`}>{example.tag}</Link>
          </>
        )}
      </p>
    </div>
  );
}

export { SubjectGroupExample };

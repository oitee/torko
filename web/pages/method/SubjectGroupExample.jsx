import React from "react";
import { Link } from "react-router-dom";
import Chip from "../../components/Chip.jsx";
import { formatNumber } from "../../assets/js/format.js";
import "./MethodExample.css";
import "./SubjectGroupExample.css";

// SubjectGroupExample shows how different names of one subject become one specific subject, and how
// that subject sits under a broad tag. The example comes from /api/method → examples.subject_group.
export default function SubjectGroupExample({ example }) {
  const names = Array.isArray(example?.names) ? example.names : [];
  if (!example?.label || names.length === 0) return null;

  return (
    <div className="group-example">
      <div className="method-box">
        <p className="method-box__label">
          Names in different speeches{example.n_names > names.length ? ` · ${names.length} of ${formatNumber(example.n_names)}` : ""}
        </p>
        <ul className="group-example__names">
          {names.map((n) => (
            <li key={n}>
              <Chip label={n} />
            </li>
          ))}
        </ul>
      </div>
      <div className="method-arrow" aria-hidden="true">
        ↓
      </div>
      <div className="method-box method-after">
        <p className="method-box__label">One specific subject</p>
        <p className="group-example__subject">
          {example.label}
          {example.speeches != null && (
            <span className="group-example__count"> · {formatNumber(example.speeches)} speeches</span>
          )}
        </p>
      </div>
      {example.tag && (
        <>
          <div className="method-arrow" aria-hidden="true">
            ↓
          </div>
          <div className="method-box method-after">
            <p className="method-box__label">Under the tag</p>
            <div>
              <Chip label={example.tag} href={`/tag/${example.tag_slug}`} />
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export { SubjectGroupExample };

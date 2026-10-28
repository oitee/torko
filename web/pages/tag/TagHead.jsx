import React from "react";
import { formatNumber } from "../../assets/js/format.js";
import "./TagHead.css";

// Formats a date range into a year span with an en-dash.
export function formatSpan(first, last) {
  const y1 = first ? String(first).split("-")[0] : null;
  const y2 = last ? String(last).split("-")[0] : null;
  if (y1 && y2) {
    return y1 === y2 ? y1 : `${y1}–${y2}`;
  }
  return y1 || y2 || null;
}

// TagHead renders the tag title, kicker, description, and four summary counts.
export default function TagHead({ tag }) {
  if (!tag) return null;

  const span = formatSpan(tag.first, tag.last);

  const numbers = [
    tag.total != null
      ? { label: "speeches", value: formatNumber(tag.total) }
      : null,
    tag.n_members != null
      ? { label: "members spoke", value: formatNumber(tag.n_members) }
      : null,
    tag.n_subjects != null && tag.n_subjects > 0
      ? { label: "subjects under this tag", value: formatNumber(tag.n_subjects) }
      : null,
    span
      ? { label: "first and latest speech", value: span }
      : null,
  ].filter(Boolean);

  return (
    <div className="tag-head">
      <div className="tag-head__header">
        <p className="tag-head__kicker">Tag</p>
        <h1 className="tag-head__title">{tag.name}</h1>
        {tag.description && (
          <p className="tag-head__description">{tag.description}</p>
        )}
      </div>

      {numbers.length > 0 && (
        <dl className="tag-head__numbers">
          {numbers.map((item, idx) => (
            <div key={idx} className="tag-head__stat">
              <dt className="tag-head__stat-label">{item.label}</dt>
              <dd className="tag-head__stat-value">{item.value}</dd>
            </div>
          ))}
        </dl>
      )}
    </div>
  );
}

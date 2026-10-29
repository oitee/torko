import React from "react";
import { formatNumber, ordinal } from "../../assets/js/format.js";
import "./HomeFigures.css";

// The range of terms in running text (e.g. 13th–18th Lok Sabha). The terms come from the API.
export function termRange(terms) {
  const list = (Array.isArray(terms) ? terms : []).map(Number).filter((n) => !Number.isNaN(n));
  if (list.length === 0) return "";
  const lo = Math.min(...list);
  const hi = Math.max(...list);
  return lo === hi ? `${ordinal(lo)} Lok Sabha` : `${ordinal(lo)}–${ordinal(hi)} Lok Sabha`;
}

// HomeFigures shows the site figures from /api/home → corpus. Each label says what the figure counts.
// No figure is written by hand: a missing field hides its row.
export default function HomeFigures({ corpus }) {
  if (!corpus) return null;

  const terms = Array.isArray(corpus.terms) ? corpus.terms : [];
  const err = corpus.error_rate;

  const rows = [
    corpus.debates != null && {
      key: "debates",
      value: formatNumber(corpus.debates),
      label: "debates read from sansad.in",
    },
    corpus.members != null && {
      key: "members",
      value: formatNumber(corpus.members),
      label:
        terms.length > 0
          ? `members with at least one speech, in ${terms.length} terms (${termRange(terms)})`
          : "members with at least one speech",
    },
    corpus.tags != null && {
      key: "tags",
      value: formatNumber(corpus.tags),
      label: "tags for the subjects of the speeches",
    },
    err?.text && {
      key: "error",
      value: err.text,
      label: err.counts ? `of ${err.counts}` : "",
    },
  ].filter(Boolean);

  if (rows.length === 0) return null;

  return (
    <dl className="home-figures">
      {rows.map((row) => (
        <div key={row.key} className="home-figures__item" data-testid={`figure-${row.key}`}>
          <dt className="home-figures__label">{row.label}</dt>
          <dd className="home-figures__value">{row.value}</dd>
        </div>
      ))}
    </dl>
  );
}

export { HomeFigures };

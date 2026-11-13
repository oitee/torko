import React from "react";
import { Link } from "react-router-dom";
import { formatNumber } from "../../assets/js/format.js";

export default function MemberMargin({ member, speechesData }) {
  if (!member) return null;

  const id = member.id;
  const speeches = member.speeches || 0;
  const terms = member.terms || [];
  const tagged = member.tagged_speeches;
  const words = terms.reduce((sum, t) => sum + (Number(t.words) || 0), 0);
  const kinds = (speechesData?.facets?.kind || []).filter((k) => k.n > 0);
  const search = (extra) => `/search?member=${id}${extra ? `&${extra}` : ""}`;

  const countRows = [
    { n: formatNumber(speeches), t: `speeches in ${terms.length} ${terms.length === 1 ? "term" : "terms"}`, to: search() },
    tagged != null ? { n: formatNumber(tagged), t: `of ${formatNumber(speeches)} speeches carry a tag` } : null,
    words > 0 ? { n: formatNumber(words), t: `words in ${formatNumber(speeches)} speeches` } : null,
  ].filter(Boolean);

  const firstYear = terms[0]?.first ? String(terms[0].first).slice(0, 4) : null;
  const lastYear = terms[terms.length - 1]?.last ? String(terms[terms.length - 1].last).slice(0, 4) : null;
  const recordSpan = firstYear && lastYear ? (firstYear === lastYear ? firstYear : `${firstYear}–${lastYear}`) : "";

  return (
    <div className="member-margin">
      <section className="member-margin__section">
        <h2 className="member-margin__heading">Counts</h2>
        <dl className="member-margin__counts">
          {countRows.map((row) => (
            <div key={row.t} className="member-margin__count-row">
              <dt className="member-margin__count-n mono">
                {row.to ? <Link to={row.to}>{row.n}</Link> : row.n}
              </dt>
              <dd className="member-margin__count-text">{row.t}</dd>
            </div>
          ))}
        </dl>

        {kinds.length > 0 && (
          <>
            <h3 className="member-margin__subheading">Speeches by debate type, of {formatNumber(speeches)}</h3>
            <dl className="member-margin__counts" aria-label="Speeches by debate type">
              {kinds.map((k) => (
                <div key={k.kind} className="member-margin__count-row">
                  <dt className="member-margin__count-n mono">
                    <Link to={search(`kind=${k.kind}`)}>{formatNumber(k.n)}</Link>
                  </dt>
                  <dd className="member-margin__count-text">{k.label || k.kind}</dd>
                </div>
              ))}
            </dl>
          </>
        )}

      </section>

      <section className="member-margin__section">
        <h2 className="member-margin__heading">Source</h2>
        <dl className="member-margin__source">
          <div className="member-margin__source-row">
            <dt>Record</dt>
            <dd>
              Lok Sabha Debates
              {recordSpan && <span className="mono">, {recordSpan}</span>}
            </dd>
          </div>
          <div className="member-margin__source-row">
            <dt>Party</dt>
            <dd>Lok Sabha member list, by term</dd>
          </div>
        </dl>
      </section>
    </div>
  );
}

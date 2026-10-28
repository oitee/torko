import React from "react";
import { formatNumber } from "../../assets/js/format.js";
import HowTorkoCounts from "../../components/HowTorkoCounts.jsx";

export default function MemberMargin({ member, speechesData }) {
  if (!member) return null;

  const speeches = member.speeches || 0;
  const terms = member.terms || [];
  const taggedSpeeches = member.tagged_speeches;

  // Extract Rule 377 count from kind facet if available
  const kindFacets = speechesData?.facets?.kind || [];
  const r377Facet = kindFacets.find(
    (k) => k.kind === "rule_377" || k.kind === "r377"
  );
  const r377Count = r377Facet ? r377Facet.n : null;

  const countRows = [
    {
      n: formatNumber(speeches),
      t: `speeches over ${terms.length} ${terms.length === 1 ? "term" : "terms"}`,
    },
    taggedSpeeches != null
      ? {
          n: formatNumber(taggedSpeeches),
          t: `of ${formatNumber(speeches)} carry a tag`,
        }
      : null,
    r377Count != null
      ? {
          n: formatNumber(r377Count),
          t: "matters raised under Rule 377",
        }
      : null,
  ].filter(Boolean);

  // Compute year span for record
  const firstDate =
    terms[0]?.first ||
    (member.recent && member.recent.length > 0
      ? member.recent[member.recent.length - 1].date
      : null);
  const lastDate =
    terms[terms.length - 1]?.last ||
    (member.recent && member.recent.length > 0
      ? member.recent[0].date
      : null);

  const firstYear = firstDate ? String(firstDate).split("-")[0] : null;
  const lastYear = lastDate ? String(lastDate).split("-")[0] : null;
  const recordSpan =
    firstYear && lastYear
      ? firstYear === lastYear
        ? firstYear
        : `${firstYear}–${lastYear}`
      : "2014–2026";

  return (
    <div className="member-margin">
      <section className="member-margin__section">
        <h2 className="member-margin__heading">Counts</h2>
        <dl className="member-margin__counts">
          {countRows.map((row, idx) => (
            <div key={idx} className="member-margin__count-row">
              <dt className="member-margin__count-n mono">{row.n}</dt>
              <dd className="member-margin__count-text mono">{row.t}</dd>
            </div>
          ))}
        </dl>
        <HowTorkoCounts>
          A speech is one time the member speaks, from their name to the next speaker's name. Short breaks from other members or the chair do not split it.
        </HowTorkoCounts>
      </section>

      <section className="member-margin__section">
        <h2 className="member-margin__heading">Source</h2>
        <dl className="member-margin__source mono">
          <div className="member-margin__source-row">
            <dt>Record</dt>
            <dd>Lok Sabha Debates, {recordSpan}</dd>
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

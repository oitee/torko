import React from "react";
import { Link } from "react-router-dom";
import { formatMonthYear } from "./PlaceHead.jsx";
import { ordinal, termYears } from "../../assets/js/format.js";
import PartyLink from "../../components/PartyLink.jsx";

// The months in which the member spoke for this seat, for example "spoke Dec 2014 to Feb 2019", or "spoke in Dec 2003" for one month.
export function spokeText(first, last) {
  if (!first || !last) return null;
  const a = formatMonthYear(first);
  const b = formatMonthYear(last);
  return a === b ? `spoke in ${a}` : `spoke ${a} to ${b}`;
}

export default function PlaceHolders({ holders = [] }) {
  const safeHolders = Array.isArray(holders) ? holders : [];
  if (safeHolders.length === 0) {
    return null;
  }

  // Group holders by term
  const termMap = new Map();
  for (const h of safeHolders) {
    const t = Number(h.term);
    if (!termMap.has(t)) {
      termMap.set(t, []);
    }
    termMap.get(t).push(h);
  }

  const terms = Array.from(termMap.keys()).sort((a, b) => a - b);

  return (
    <section
      className="place-section place-holders"
      aria-labelledby="holders-heading"
    >
      <div className="section-header">
        <h2 id="holders-heading" className="place-section__title">
          MPs of this seat who spoke in the House
        </h2>
        <span className="place-section__meta mono">Across all terms</span>
      </div>

      <div className="place-holders__list">
        {terms.map((term) => {
          const items = termMap.get(term) || [];
          const termLabel = ordinal(term);
          const years = termYears(term);

          return (
            <div key={term} className="place-holders__row">
              <div className="place-holders__term-col mono">
                <span className="place-holders__term-name">{termLabel}</span>
                {years && <span className="place-holders__term-years"> · {years}</span>}
              </div>

              <div className="place-holders__items-col">
                {items.map((h, idx) => {
                  const sinceText = h.since ? `in office from ${formatMonthYear(h.since)}` : null;
                  const dates = [sinceText, spokeText(h.first_spoke, h.last_spoke)].filter(Boolean).join(" · ");

                  return (
                    <div
                      key={h.id || idx}
                      className="place-holders__holder"
                    >
                      <Link
                        to={`/member/${h.id}`}
                        className="place-holders__name"
                      >
                        {h.name}
                      </Link>

                      {h.party && (
                        <span className="place-holders__party">
                          <PartyLink code={h.party} />
                        </span>
                      )}

                      {dates && (
                        <span className="place-holders__spoke mono">
                          {dates}
                        </span>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}

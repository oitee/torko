import React from "react";
import { Link } from "react-router-dom";
import { formatMonthYear } from "./PlaceHead.jsx";
import { termOrdinal } from "./PlaceWhen.jsx";

const TERM_YEARS = {
  13: "1999–2004",
  14: "2004–09",
  15: "2009–14",
  16: "2014–19",
  17: "2019–24",
  18: "2024–",
};

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
      <div className="place-section__header">
        <h2 id="holders-heading" className="place-section__title">
          MPs for this seat
        </h2>
        <span className="place-section__meta mono">Across all terms</span>
      </div>

      <div className="place-holders__list">
        {terms.map((term) => {
          const items = termMap.get(term) || [];
          const termLabel = termOrdinal(term);
          const years = TERM_YEARS[term] || "";

          return (
            <div key={term} className="place-holders__row">
              <div className="place-holders__term-col">
                <span className="place-holders__term-name mono">{termLabel}</span>
                {years && (
                  <span className="place-holders__term-years mono">{years}</span>
                )}
              </div>

              <div className="place-holders__items-col">
                {items.map((h, idx) => {
                  const spokeText =
                    h.first_spoke && h.last_spoke
                      ? `spoke from ${formatMonthYear(h.first_spoke)} to ${formatMonthYear(h.last_spoke)}`
                      : null;

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
                          {h.party}
                        </span>
                      )}

                      {h.state && (
                        <span className="place-holders__state">
                          {h.state}
                        </span>
                      )}

                      {spokeText && (
                        <span className="place-holders__spoke mono">
                          {spokeText}
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

import React, { useState } from "react";
import { formatNumber } from "../../assets/js/format.js";

// Suffix for term number (13 -> "13th").
export function termOrdinal(n) {
  const num = Math.abs(parseInt(n, 10));
  const mod100 = num % 100;
  if (mod100 >= 11 && mod100 <= 13) return `${n}th`;
  const mod10 = num % 10;
  if (mod10 === 1) return `${n}st`;
  if (mod10 === 2) return `${n}nd`;
  if (mod10 === 3) return `${n}rd`;
  return `${n}th`;
}

const TERM_DEFAULTS = [
  { term: 13, start: 1999, end: 2004, yearsFull: "1999–2004", yearsShort: "1999–04" },
  { term: 14, start: 2004, end: 2009, yearsFull: "2004–2009", yearsShort: "2004–09" },
  { term: 15, start: 2009, end: 2014, yearsFull: "2009–2014", yearsShort: "2009–14" },
  { term: 16, start: 2014, end: 2019, yearsFull: "2014–2019", yearsShort: "2014–19" },
  { term: 17, start: 2019, end: 2024, yearsFull: "2019–2024", yearsShort: "2019–24" },
  { term: 18, start: 2024, end: null, yearsFull: "2024–", yearsShort: "2024–" },
];

export default function PlaceWhen({
  sessions = [],
  totalSpeeches = 0,
  selectedSession = null,
  onToggleSession,
}) {
  const [hoverKey, setHoverKey] = useState(null);

  const safeSessions = Array.isArray(sessions) ? sessions : [];
  if (safeSessions.length === 0) return null;

  // Find max session count to scale bars and determine y-ticks.
  const smax = Math.max(1, ...safeSessions.map((s) => Number(s.n) || 0));
  const ymax =
    smax <= 4 ? 4 : smax <= 6 ? 6 : smax <= 10 ? 10 : Math.ceil(smax / 10) * 10;
  const yTicks = [ymax, Math.round(ymax / 2), 0];

  // Group sessions by term
  const termMap = new Map();
  for (const info of TERM_DEFAULTS) {
    termMap.set(info.term, {
      ...info,
      sessions: [],
    });
  }

  for (const s of safeSessions) {
    const t = Number(s.term);
    if (!termMap.has(t)) {
      termMap.set(t, {
        term: t,
        start: s.year || 2000,
        end: null,
        yearsFull: s.year ? `${s.year}–` : "",
        yearsShort: s.year ? `${s.year}–` : "",
        sessions: [],
      });
    }
    termMap.get(t).sessions.push(s);
  }

  const termGroups = Array.from(termMap.values()).filter(
    (g) => g.sessions.length > 0
  );

  // Total sessions for positioning tooltips near edges
  const allSessionKeys = safeSessions.map((s) => `${s.term}-${s.session}`);

  return (
    <section className="place-section place-when" aria-labelledby="when-heading">
      <div className="place-section__header">
        <h2 id="when-heading" className="place-section__title">
          When
        </h2>
        <span className="place-section__meta mono">
          Across all terms · of {formatNumber(totalSpeeches)} speeches
        </span>
      </div>

      <div className="place-when__card">
        <div className="place-when__card-head">
          <h3 className="place-when__card-title">Speeches per session</h3>
          <span className="place-when__card-meta mono">13th to 18th Lok Sabha</span>
        </div>

        <div className="place-when__chart-scroll">
          <div className="place-when__chart-grid">
            {/* Y axis ticks column */}
            <div className="place-when__y-axis" aria-hidden="true">
              {yTicks.map((v) => {
                const bottomPercent = (v / ymax) * 100;
                return (
                  <span
                    key={v}
                    className="place-when__y-label mono"
                    style={{ bottom: `calc(${bottomPercent}% - 7px)` }}
                  >
                    {v}
                  </span>
                );
              })}
            </div>

            {/* Chart plotting area */}
            <div className="place-when__plot-area">
              {/* Horizontal grid lines */}
              <div className="place-when__grid-lines" aria-hidden="true">
                {yTicks.map((v) => {
                  const bottomPercent = (v / ymax) * 100;
                  return (
                    <span
                      key={v}
                      className={`place-when__grid-line ${v === 0 ? "place-when__grid-line--base" : ""}`}
                      style={{ bottom: `${bottomPercent}%` }}
                    />
                  );
                })}
              </div>

              {/* Term grouped columns */}
              <div
                role="group"
                aria-label="Speeches per session"
                className="place-when__groups"
              >
                {termGroups.map((g, ti) => {
                  const groupKey = `term-${g.term}`;
                  return (
                    <div
                      key={groupKey}
                      className={`place-when__group ${ti > 0 ? "place-when__group--bordered" : ""}`}
                      style={{ flex: `${g.sessions.length} ${g.sessions.length} 0` }}
                    >
                      <div className="place-when__bars-row">
                        {g.sessions.map((s) => {
                          const key = `${s.term}-${s.session}`;
                          const isSelected = selectedSession === key;
                          const isHovered = hoverKey === key;
                          const isHot = isSelected || isHovered;
                          const heightPercent = s.n
                            ? Math.max(2, (s.n / ymax) * 100)
                            : 0;

                          const idx = allSessionKeys.indexOf(key);
                          const edge =
                            idx < 4
                              ? "left"
                              : idx > allSessionKeys.length - 5
                              ? "right"
                              : "center";

                          return (
                            <button
                              key={key}
                              type="button"
                              className={`place-when__bar-slot ${isSelected ? "place-when__bar-slot--selected" : ""}`}
                              aria-pressed={isSelected}
                              aria-label={`${termOrdinal(s.term)} LS, session ${s.session}, ${s.year || ""}, ${s.n} speeches`}
                              onClick={() => onToggleSession && onToggleSession(s)}
                              onMouseEnter={() => setHoverKey(key)}
                              onMouseLeave={() => {
                                if (hoverKey === key) setHoverKey(null);
                              }}
                              onFocus={() => setHoverKey(key)}
                              onBlur={() => {
                                if (hoverKey === key) setHoverKey(null);
                              }}
                            >
                              <span
                                className={`place-when__bar ${isHot ? "place-when__bar--hot" : ""}`}
                                style={{ height: `${heightPercent}%` }}
                              />

                              {isHovered && (
                                <span
                                  aria-hidden="true"
                                  className={`place-when__tip place-when__tip--${edge}`}
                                  style={{
                                    bottom: `calc(${Math.min(100, heightPercent)}% + 6px)`,
                                  }}
                                >
                                  <strong className="place-when__tip-title">
                                    {termOrdinal(s.term)} LS, session {s.session}
                                  </strong>
                                  <span className="place-when__tip-sub">
                                    {s.year || ""} · {formatNumber(s.n)}{" "}
                                    {s.n === 1 ? "speech" : "speeches"}
                                  </span>
                                </span>
                              )}
                            </button>
                          );
                        })}
                      </div>

                      {/* Term label below bars */}
                      <div className="place-when__group-foot">
                        <span className="place-when__term-label mono">
                          {termOrdinal(g.term)} LS
                        </span>
                        <span className="place-when__term-years mono">
                          {g.yearsFull}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="place-when__bottom">
        <p className="place-when__hint">
          Pick a session to read its speeches. An empty slot means no speech
          named this place in that session.
        </p>

        <details className="place-when__details">
          <summary className="place-when__summary">Show as table</summary>
          <div className="place-when__table-wrap">
            <table className="place-when__table mono">
              <thead>
                <tr>
                  <th scope="col" className="place-when__th-term">
                    Term
                  </th>
                  <th scope="col" className="place-when__th-years">
                    Years
                  </th>
                  <th scope="col" className="place-when__th-active">
                    Sessions with a speech
                  </th>
                  <th scope="col" className="place-when__th-speeches">
                    Speeches
                  </th>
                </tr>
              </thead>
              <tbody>
                {termGroups.map((g) => {
                  const activeCount = g.sessions.filter((s) => (Number(s.n) || 0) > 0).length;
                  const termTotal = g.sessions.reduce(
                    (sum, s) => sum + (Number(s.n) || 0),
                    0
                  );
                  return (
                    <tr key={g.term}>
                      <td className="place-when__td-term">{termOrdinal(g.term)}</td>
                      <td className="place-when__td-years">{g.yearsShort}</td>
                      <td className="place-when__td-active">
                        {activeCount} of {g.sessions.length}
                      </td>
                      <td className="place-when__td-speeches">
                        {formatNumber(termTotal)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </details>
      </div>
    </section>
  );
}

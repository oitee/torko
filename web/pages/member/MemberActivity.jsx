import React, { useId, useState } from "react";
import { formatNumber, termLong, termShort } from "../../assets/js/format.js";
import Button from "../../components/Button.jsx";

export default function MemberActivity({
  sessions = [],
  terms = [],
  selectedSession = null,
  onSelectSession,
}) {
  const [showTable, setShowTable] = useState(false);
  const [activeSession, setActiveSession] = useState(null);
  const tableId = useId();

  if (!Array.isArray(sessions) || sessions.length === 0) {
    return null;
  }

  // Count a as the sessions where n is more than house_median
  const aboveCount = sessions.filter(
    (s) => s.n > (s.house_median != null ? s.house_median : 0)
  ).length;

  // Find busiest session
  const busiest = sessions.reduce(
    (max, s) => (s.n > max.n ? s : max),
    sessions[0]
  );

  const sentence = `Above the typical member in ${aboveCount} of ${sessions.length} sessions.${
    busiest && busiest.n > 0
      ? ` Busiest: ${busiest.label}, with ${formatNumber(busiest.n)} speeches.`
      : ""
  }`;

  // Max value for y-axis
  const topVal = Math.max(
    1,
    ...sessions.map((s) => Math.max(s.n || 0, s.house_median || 0))
  );
  const yMax =
    topVal <= 4
      ? 4
      : topVal <= 6
      ? 6
      : topVal <= 10
      ? 10
      : Math.ceil(topVal / 10) * 10;
  const yTicks = [yMax, Math.round(yMax / 2), 0];

  // Group sessions by term
  const termMap = new Map();
  sessions.forEach((s) => {
    const t = s.term;
    if (!termMap.has(t)) {
      termMap.set(t, []);
    }
    termMap.get(t).push(s);
  });

  const termGroups = Array.from(termMap.entries()).map(([termNum, sessList]) => {
    const termObj = terms.find((t) => t.term === termNum);
    const party =
      termObj?.parties && termObj.parties.length > 0
        ? termObj.parties.join(", ")
        : null;
    const label = party
      ? `${termShort(termNum)} · ${party}`
      : termLong(termNum);
    return {
      term: termNum,
      label,
      sessions: sessList,
    };
  });

  return (
    <section className="member-activity" id="activity" aria-labelledby="member-activity-heading">
      <div className="member-section-head">
        <div className="member-section-head__text">
          <h2 id="member-activity-heading" className="member-section-title">
            Activity
          </h2>
          <p className="member-section-subtitle">{sentence}</p>
        </div>
        <Button
          variant="secondary"
          onClick={() => setShowTable((prev) => !prev)}
          aria-expanded={showTable}
          aria-controls={tableId}
        >
          {showTable ? "Show as chart" : "Show as table"}
        </Button>
      </div>

      <div className="member-activity__container">
        <div className="member-activity__header">
          <h3 className="member-activity__title">Speeches per session</h3>
          <div className="member-activity__legend mono">
            <span className="member-activity__legend-bar" aria-hidden="true" />
            <span>Member</span>
            <span className="member-activity__legend-line" aria-hidden="true" />
            <span>typical MP in the house</span>
          </div>
        </div>

        {showTable ? (
          <div id={tableId} className="member-activity__table-wrap">
            <table className="member-activity__table">
              <thead>
                <tr>
                  <th scope="col">Term</th>
                  <th scope="col">Session</th>
                  <th scope="col" className="text-right">Member speeches</th>
                  <th scope="col" className="text-right">House median</th>
                </tr>
              </thead>
              <tbody>
                {sessions.map((s, idx) => (
                  <tr key={idx}>
                    <td>{termShort(s.term)}</td>
                    <td>{s.label}</td>
                    <td className="text-right mono">{formatNumber(s.n)}</td>
                    <td className="text-right mono">
                      {s.house_median != null ? formatNumber(s.house_median) : "–"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="member-activity__charts">
            {/* Desktop / Wide Chart */}
            <div className="member-activity__chart-wide">
              <div className="member-activity__y-axis">
                {yTicks.map((v) => (
                  <span
                    key={v}
                    className="member-activity__y-tick mono"
                    style={{ bottom: `calc(${(v / yMax) * 100}% - 7px)` }}
                  >
                    {v}
                  </span>
                ))}
              </div>

              <div className="member-activity__plot">
                {/* Background Grid Lines */}
                <div className="member-activity__gridlines" aria-hidden="true">
                  {yTicks.map((v) => (
                    <span
                      key={v}
                      className="member-activity__gridline"
                      style={{ bottom: `${(v / yMax) * 100}%` }}
                    />
                  ))}
                </div>

                {/* Term Groups */}
                <div className="member-activity__terms" role="group" aria-label="Speeches per session chart">
                  {termGroups.map((group, groupIdx) => (
                    <div
                      key={group.term}
                      className={`member-activity__term-group ${
                        groupIdx > 0 ? "member-activity__term-group--bordered" : ""
                      }`}
                      style={{ flex: `${group.sessions.length} ${group.sessions.length} 0` }}
                    >
                      <div className="member-activity__bars">
                        {group.sessions.map((s, sIdx) => {
                          const p = Math.min(100, Math.max(0, (s.n / yMax) * 100));
                          const medP =
                            s.house_median != null
                              ? Math.min(100, Math.max(0, (s.house_median / yMax) * 100))
                              : 0;
                          const isHovered = activeSession === s;
                          const isSelected = selectedSession === `${s.term}-${s.session}`;
                          const ariaLabel = `${s.label}: ${s.n} speeches, house median ${
                            s.house_median != null ? s.house_median : "none"
                          }`;

                          return (
                            <button
                              type="button"
                              key={sIdx}
                              className={`member-activity__bar-slot${
                                isSelected ? " member-activity__bar-slot--selected" : ""
                              }`}
                              onMouseEnter={() => setActiveSession(s)}
                              onMouseLeave={() => setActiveSession(null)}
                              onFocus={() => setActiveSession(s)}
                              onBlur={() => setActiveSession(null)}
                              onClick={() => onSelectSession && onSelectSession(s)}
                              aria-pressed={isSelected}
                              aria-label={ariaLabel}
                            >
                              {s.n > 0 && (
                                <span
                                  className={`member-activity__bar ${
                                    isHovered ? "member-activity__bar--hovered" : ""
                                  }`}
                                  style={{ height: `max(2px, ${p}%)` }}
                                />
                              )}
                              {s.house_median != null && (
                                <span
                                  className="member-activity__median-line"
                                  style={{ bottom: `calc(${medP}% - 1px)` }}
                                />
                              )}
                              {isHovered && (
                                <div className="member-activity__tooltip mono" role="tooltip">
                                  <strong>{s.label}</strong>
                                  <span>
                                    {s.n} speeches · median {s.house_median}
                                  </span>
                                </div>
                              )}
                            </button>
                          );
                        })}
                      </div>

                      <div className="member-activity__term-footer mono">
                        <span className="member-activity__term-title">{group.label}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Mobile / Narrow Chart */}
            <div className="member-activity__chart-narrow">
              {termGroups.map((group) => (
                <div key={group.term} className="member-activity__narrow-group">
                  <div className="member-activity__narrow-term-head mono">
                    <span>{group.label}</span>
                  </div>
                  <div className="member-activity__narrow-rows">
                    {group.sessions.map((s, sIdx) => {
                      const p = Math.min(100, Math.max(0, (s.n / yMax) * 100));
                      const medP =
                        s.house_median != null
                          ? Math.min(100, Math.max(0, (s.house_median / yMax) * 100))
                          : 0;
                      return (
                        <button
                          type="button"
                          key={sIdx}
                          className={`member-activity__narrow-row${
                            selectedSession === `${s.term}-${s.session}`
                              ? " member-activity__narrow-row--selected"
                              : ""
                          }`}
                          aria-pressed={selectedSession === `${s.term}-${s.session}`}
                          onClick={() => onSelectSession && onSelectSession(s)}
                        >
                          <span className="member-activity__narrow-label mono">
                            {s.label}
                          </span>
                          <div className="member-activity__narrow-bar-track">
                            {s.n > 0 && (
                              <span
                                className="member-activity__narrow-bar"
                                style={{ width: `max(2px, ${p}%)` }}
                              />
                            )}
                            {s.house_median != null && (
                              <span
                                className="member-activity__narrow-med"
                                style={{ left: `calc(${medP}% - 1px)` }}
                              />
                            )}
                          </div>
                          <span className="member-activity__narrow-count mono">
                            {s.n}
                          </span>
                        </button>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {(() => {
          const picked = selectedSession
            ? sessions.find((x) => `${x.term}-${x.session}` === selectedSession)
            : null;
          if (!picked) return null;
          return (
            <p className="member-activity__selected" role="status">
              <span>
                The list of speeches shows {picked.label}: {formatNumber(picked.n)}{" "}
                {picked.n === 1 ? "speech" : "speeches"}.
              </span>{" "}
              <a href="#speeches" className="member-activity__selected-link">
                Go to the speeches
              </a>{" "}
              <button
                type="button"
                className="button button--text"
                onClick={() => onSelectSession && onSelectSession(picked)}
              >
                Show all sessions
              </button>
            </p>
          );
        })()}

        <div className="member-activity__note meta">
          Pick a session to read its speeches. The green line is the median member in that session.
        </div>
      </div>
    </section>
  );
}

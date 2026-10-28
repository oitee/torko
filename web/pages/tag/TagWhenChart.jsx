import React, { useState } from "react";
import Button from "../../components/Button.jsx";
import { formatNumber } from "../../assets/js/format.js";
import "./TagWhenChart.css";

const TERM_RANGES = {
  13: [1999, 2004],
  14: [2004, 2009],
  15: [2009, 2014],
  16: [2014, 2019],
  17: [2019, 2024],
  18: [2024, 2029],
};

// TagWhenChart draws the annual distribution of speeches as single bars.
export default function TagWhenChart({ sessions = [], selectedTerm = "" }) {
  const [showTable, setShowTable] = useState(false);
  const [hoverData, setHoverData] = useState(null);

  const safeSessions = Array.isArray(sessions) ? sessions : [];
  const yearsInSessions = safeSessions
    .map((s) => Number(s.year))
    .filter((y) => !Number.isNaN(y) && y > 1900);

  if (yearsInSessions.length === 0) {
    return null;
  }

  const minYear = Math.min(...yearsInSessions);
  const maxYear = Math.max(...yearsInSessions);
  const totalYears = maxYear - minYear + 1;

  // Build year buckets from minYear through maxYear
  const yearData = [];
  for (let y = minYear; y <= maxYear; y++) {
    const matching = safeSessions.filter((s) => Number(s.year) === y);
    const n = matching.reduce((sum, s) => sum + (Number(s.n) || 0), 0);
    const terms = new Set(matching.map((s) => Number(s.term)));

    let inTerm = true;
    if (selectedTerm && selectedTerm !== "all") {
      const termNum = Number(selectedTerm);
      const range = TERM_RANGES[termNum];
      inTerm =
        terms.has(termNum) ||
        (Boolean(range) && y >= range[0] && y <= range[1]);
    }

    yearData.push({ year: y, n, inTerm });
  }

  const maxN = Math.max(1, ...yearData.map((d) => d.n));

  const readoutText = hoverData
    ? `${hoverData.year} · ${formatNumber(hoverData.n)} ${
        hoverData.n === 1 ? "speech" : "speeches"
      }`
    : "Hover a year for the count";

  return (
    <section className="tag-when-chart" aria-labelledby="when-heading">
      <div className="tag-when-chart__header">
        <h2 id="when-heading" className="tag-when-chart__title">
          When
        </h2>
        <span className="tag-when-chart__readout mono">{readoutText}</span>
      </div>

      <div className="tag-when-chart__box">
        {/* Visual Chart */}
        <div
          className={`tag-when-chart__visual ${showTable ? "sr-only" : ""}`}
          aria-hidden={showTable ? "true" : undefined}
        >
          <div
            className="tag-when-chart__plot"
            style={{
              gridTemplateColumns: `repeat(${totalYears}, minmax(0, 1fr))`,
            }}
            onMouseLeave={() => setHoverData(null)}
          >
            {yearData.map((d, index) => {
              const heightPercent = maxN > 0 ? (d.n / maxN) * 100 : 0;
              const isHovered = hoverData?.year === d.year;

              return (
                <div
                  key={d.year}
                  className={`tag-when-chart__col ${
                    !d.inTerm ? "tag-when-chart__col--faded" : ""
                  } ${isHovered ? "tag-when-chart__col--hovered" : ""}`}
                  style={{ height: `${heightPercent}%` }}
                  onMouseEnter={() => setHoverData(d)}
                  tabIndex={0}
                  role="img"
                  aria-label={`${d.year}: ${d.n} speeches`}
                  onFocus={() => setHoverData(d)}
                  onBlur={() => setHoverData(null)}
                  data-testid={`year-col-${d.year}`}
                >
                  <div className="tag-when-chart__bar" />
                </div>
              );
            })}
          </div>

          <div
            className="tag-when-chart__axis mono"
            style={{
              gridTemplateColumns: `repeat(${totalYears}, minmax(0, 1fr))`,
            }}
          >
            <span style={{ gridColumn: 1 }} className="tag-when-chart__axis-min">
              {minYear}
            </span>
            <span
              style={{ gridColumn: totalYears }}
              className="tag-when-chart__axis-max"
            >
              {maxYear}
            </span>
          </div>
        </div>

        {/* Accessible Data Table */}
        <table
          className={`tag-when-chart__table ${showTable ? "" : "sr-only"}`}
        >
          <caption>Speeches per year</caption>
          <thead>
            <tr>
              <th scope="col">Year</th>
              <th scope="col">Speeches</th>
            </tr>
          </thead>
          <tbody>
            {yearData.map((d) => (
              <tr key={d.year}>
                <td>{d.year}</td>
                <td>{formatNumber(d.n)}</td>
              </tr>
            ))}
          </tbody>
        </table>

        <div className="tag-when-chart__toggle">
          <Button variant="text" onClick={() => setShowTable((prev) => !prev)}>
            {showTable ? "Show as chart" : "Show as table"}
          </Button>
        </div>
      </div>
    </section>
  );
}

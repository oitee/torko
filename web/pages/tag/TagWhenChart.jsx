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

// The rate of each year: speeches with the tag per 1,000 tagged speeches of that year.
// A year with no tagged speech has no rate.
export function yearRates(years) {
  const list = Array.isArray(years) ? years : [];
  return list
    .map((y) => {
      const n = Number(y.n) || 0;
      const tagged = Number(y.tagged) || 0;
      return { year: Number(y.year), n, tagged, per1000: tagged > 0 ? (1000 * n) / tagged : null };
    })
    .filter((y) => !Number.isNaN(y.year))
    .sort((a, b) => a.year - b.year);
}

// The rate with one decimal, for example "4.2".
export function formatRate(per1000) {
  return per1000 === null || per1000 === undefined ? "–" : per1000.toFixed(1);
}

// One sentence for a year, for example "2014: 4.2 in every 1,000 tagged speeches (12 speeches)".
export function yearReadout(d) {
  if (d.tagged === 0) return `${d.year}: no tagged speeches`;
  if (d.n === 0) return `${d.year}: no speech with this tag`;
  const count = d.n === 1 ? "1 speech" : `${formatNumber(d.n)} speeches`;
  return `${d.year}: ${formatRate(d.per1000)} in every 1,000 tagged speeches (${count})`;
}

// TagWhenChart draws one bar for each year. The height is the rate per 1,000 tagged speeches of the year,
// so a year does not look bigger only because it has more speeches. Each speech counts in the year of its debate.
export default function TagWhenChart({ years = [], selectedTerm = "" }) {
  const [showTable, setShowTable] = useState(false);
  const [hoverData, setHoverData] = useState(null);

  const data = yearRates(years);
  if (data.length === 0) {
    return null;
  }

  const minYear = data[0].year;
  const maxYear = data[data.length - 1].year;
  const range = selectedTerm && selectedTerm !== "all" ? TERM_RANGES[Number(selectedTerm)] : null;
  const yearData = data.map((d) => ({ ...d, inTerm: !range || (d.year >= range[0] && d.year <= range[1]) }));
  const maxRate = Math.max(0, ...yearData.map((d) => d.per1000 || 0));
  const grid = { gridTemplateColumns: `repeat(${yearData.length}, minmax(0, 1fr))` };

  return (
    <section className="tag-when-chart" aria-labelledby="when-heading">
      <div className="tag-when-chart__header">
        <h2 id="when-heading" className="tag-when-chart__title">
          When
        </h2>
        <span className="tag-when-chart__readout mono" aria-live="polite">
          {hoverData ? yearReadout(hoverData) : "Point at a year"}
        </span>
      </div>

      <div className="tag-when-chart__box">
        <div
          className={`tag-when-chart__visual ${showTable ? "sr-only" : ""}`}
          aria-hidden={showTable ? "true" : undefined}
        >
          <div className="tag-when-chart__plot" style={grid} onMouseLeave={() => setHoverData(null)}>
            {yearData.map((d) => {
              const heightPercent = maxRate > 0 ? ((d.per1000 || 0) / maxRate) * 100 : 0;
              const isHovered = hoverData?.year === d.year;

              return (
                <div
                  key={d.year}
                  className={`tag-when-chart__col ${!d.inTerm ? "tag-when-chart__col--faded" : ""} ${
                    isHovered ? "tag-when-chart__col--hovered" : ""
                  }`}
                  style={{ height: `${heightPercent}%` }}
                  onMouseEnter={() => setHoverData(d)}
                  tabIndex={0}
                  role="img"
                  aria-label={yearReadout(d)}
                  onFocus={() => setHoverData(d)}
                  onBlur={() => setHoverData(null)}
                  data-testid={`year-col-${d.year}`}
                >
                  <div className="tag-when-chart__bar" />
                </div>
              );
            })}
          </div>

          <div className="tag-when-chart__axis mono" style={grid}>
            <span style={{ gridColumn: 1 }} className="tag-when-chart__axis-min">
              {minYear}
            </span>
            <span style={{ gridColumn: yearData.length }} className="tag-when-chart__axis-max">
              {maxYear}
            </span>
          </div>
        </div>

        <table className={`tag-when-chart__table ${showTable ? "" : "sr-only"}`}>
          <caption>Speeches with this tag per 1,000 tagged speeches, by year</caption>
          <thead>
            <tr>
              <th scope="col">Year</th>
              <th scope="col">With this tag</th>
              <th scope="col">Tagged speeches</th>
              <th scope="col">Per 1,000</th>
            </tr>
          </thead>
          <tbody>
            {yearData.map((d) => (
              <tr key={d.year}>
                <td>{d.year}</td>
                <td>{formatNumber(d.n)}</td>
                <td>{formatNumber(d.tagged)}</td>
                <td>{formatRate(d.per1000)}</td>
              </tr>
            ))}
          </tbody>
        </table>

        <p className="tag-when-chart__note">
          Each bar is one year. Its height is the number of speeches with this tag in every 1,000 tagged speeches of
          that year. A tagged speech is a speech with at least one tag of any kind.
        </p>

        <div className="tag-when-chart__toggle">
          <Button variant="text" onClick={() => setShowTable((prev) => !prev)}>
            {showTable ? "Show as chart" : "Show as table"}
          </Button>
        </div>
      </div>
    </section>
  );
}

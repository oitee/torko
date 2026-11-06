import React, { useState } from "react";
import { Link } from "react-router-dom";
import BarTip from "../../components/BarTip.jsx";
import Button from "../../components/Button.jsx";
import { TERM_SPANS, formatNumber, speechCount } from "../../assets/js/format.js";
import { peakYear, yearSeries } from "../../assets/js/years.js";
import "./TagWhenChart.css";

export function yearSearchHref(slug, year) {
  return `/search?tag=${slug}&date_from=${year}-01-01&date_to=${year}-12-31`;
}

// One sentence for a year on the Tag page, for example "2014: 23 speeches".
export function countReadout(d) {
  return `${d.year}: ${d.n === 0 ? "no speech with this tag" : speechCount(d.n)}`;
}

// TagWhenChart draws one bar for each year. The height is the count of speeches with the tag in that year.
// Each speech counts in the year of its debate. A tap or a click on a bar keeps its readout on screen.
export default function TagWhenChart({ years = [], selectedTerm = "", slug = "" }) {
  const [showTable, setShowTable] = useState(false);
  const [hoverData, setHoverData] = useState(null);
  const [pinned, setPinned] = useState(null);
  const data = yearSeries(years);
  if (data.length === 0) {
    return null;
  }

  const range = selectedTerm && selectedTerm !== "all" ? TERM_SPANS[Number(selectedTerm)] : null;
  const yearData = data.map((d) => ({ ...d, inTerm: !range || (d.year >= range[0] && d.year <= (range[1] ?? Infinity)) }));
  const maxValue = Math.max(0, ...yearData.map((d) => d.n));
  const peak = peakYear(yearData);
  const grid = { gridTemplateColumns: `repeat(${yearData.length}, minmax(0, 1fr))` };
  const formatTick = (v) => formatNumber(Math.round(v));
  const ticks = [maxValue, maxValue / 2, 0];
  // One bar is green: the bar under the pointer, else the clicked bar, else the year with the most speeches.
  // Only a bar that the reader points at or clicks shows the pop-up.
  const active = hoverData || pinned || peak;
  const picked = hoverData || pinned;
  const pickedIndex = picked ? yearData.findIndex((d) => d.year === picked.year) : -1;
  const pickedHeight = picked && maxValue > 0 ? (picked.n / maxValue) * 100 : 0;

  return (
    <section className="tag-when-chart" aria-labelledby="when-heading">
      <div className="tag-when-chart__header">
        <h2 id="when-heading" className="tag-when-chart__title">
          When
        </h2>
      </div>

      {pinned && pinned.n > 0 && slug && (
        <Link className="tag-when-chart__year-link" to={yearSearchHref(slug, pinned.year)}>
          Read the {speechCount(pinned.n)} of {pinned.year}
        </Link>
      )}

      <div className="tag-when-chart__box">
        <div
          className={`tag-when-chart__visual ${showTable ? "sr-only" : ""}`}
          aria-hidden={showTable ? "true" : undefined}
        >
          <div className="tag-when-chart__frame">
            <div className="tag-when-chart__y mono" aria-hidden="true">
              {ticks.map((v, i) => (
                <span key={i} className="tag-when-chart__y-tick" style={{ bottom: `${maxValue > 0 ? (v / maxValue) * 100 : 0}%` }}>
                  {formatTick(v)}
                </span>
              ))}
            </div>

            <div className="tag-when-chart__plot-wrap">
              <div className="tag-when-chart__gridlines" aria-hidden="true">
                {ticks.map((v, i) => (
                  <span key={i} className="tag-when-chart__gridline" style={{ bottom: `${maxValue > 0 ? (v / maxValue) * 100 : 0}%` }} />
                ))}
              </div>

              <div className="tag-when-chart__plot" style={grid} onMouseLeave={() => setHoverData(null)}>
                {yearData.map((d) => {
                  const heightPercent = maxValue > 0 ? (d.n / maxValue) * 100 : 0;
                  const isPinned = pinned?.year === d.year;
                  const isActive = active?.year === d.year;
                  const pick = () => setPinned(isPinned ? null : d);

                  return (
                    <div
                      key={d.year}
                      className={`tag-when-chart__col${!d.inTerm ? " tag-when-chart__col--faded" : ""}${
                        isActive ? " tag-when-chart__col--active" : ""
                      }`}
                      style={{ height: `${heightPercent}%` }}
                      onMouseEnter={() => setHoverData(d)}
                      tabIndex={0}
                      role="button"
                      aria-pressed={isPinned}
                      aria-label={countReadout(d)}
                      onClick={pick}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" || e.key === " ") {
                          e.preventDefault();
                          pick();
                        }
                      }}
                      onFocus={() => setHoverData(d)}
                      onBlur={() => setHoverData(null)}
                      data-testid={`year-col-${d.year}`}
                    >
                      <div className="tag-when-chart__bar" />
                    </div>
                  );
                })}
                <BarTip index={pickedIndex} count={yearData.length} heightPct={pickedHeight}>
                  {picked ? countReadout(picked) : null}
                </BarTip>
              </div>

              <div className="tag-when-chart__axis mono" style={grid} aria-hidden="true">
                {yearData.map((d, i) => (
                  <span key={d.year} className="tag-when-chart__axis-year" style={{ gridColumn: i + 1 }}>
                    {d.year % 5 === 0 ? d.year : ""}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>

        <table className={`tag-when-chart__table ${showTable ? "" : "sr-only"}`}>
          <caption>Speeches with this tag, by year</caption>
          <thead>
            <tr>
              <th scope="col">Year</th>
              <th scope="col">Speeches with this tag</th>
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

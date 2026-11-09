import React, { useState } from "react";
import BarTip from "../../components/BarTip.jsx";
import Button from "../../components/Button.jsx";
import { formatNumber, speechCount } from "../../assets/js/format.js";
import { peakYear, yearSeries } from "../../assets/js/years.js";

// A small year count gives a bar that one speech can change. The page says so below this number.
export const SMALL_MAX = 10;

// The years that get a label under the axis: each fifth year, and the first and last year when they are not too close.
// gap is the least number of bars between two labels.
export function tickYears(years, gap = 4) {
  const list = years.map((y) => y.year);
  if (list.length === 0) return [];
  const ticks = list.filter((y) => y % 5 === 0);
  const far = (y) => ticks.every((t) => Math.abs(t - y) >= gap);
  const out = [...ticks];
  if (far(list[0])) out.unshift(list[0]);
  if (far(list[list.length - 1])) out.push(list[list.length - 1]);
  return out;
}

export default function PlaceWhen({ years = [] }) {
  const [active, setActive] = useState(null);
  const [showTable, setShowTable] = useState(false);

  const data = yearSeries(years);
  if (data.length === 0) return null;

  const top = Math.max(0, ...data.map((d) => d.n));
  // The list of years is built again on each render, so the active year is found by its year, not by the object.
  const hovered = active ? data.find((d) => d.year === active.year) || null : null;
  const shown = hovered || peakYear(data);
  const total = data.reduce((sum, d) => sum + d.n, 0);
  const grid = { gridTemplateColumns: `repeat(${data.length}, minmax(0, 1fr))` };
  const first = data[0].year;
  const scaleText = (v) => formatNumber(Math.round(v));
  const readout = hovered ? `${hovered.year}: ${speechCount(hovered.n)}` : null;

  return (
    <section className="place-when" aria-labelledby="when-heading">
      <div className="section-header">
        <h2 id="when-heading" className="place-section__title">
          When
        </h2>
        <span className="place-section__meta mono">
          {formatNumber(total)} speeches, by year of the debate
        </span>
      </div>

      <div className="place-when__box">
        <div className={showTable ? "sr-only" : undefined} aria-hidden={showTable ? "true" : undefined}>
          <div className="place-when__chart">
            <div className="place-when__scale mono" aria-hidden="true">
              <span>{scaleText(top)}</span>
              <span>{scaleText(top / 2)}</span>
              <span>0</span>
            </div>
            <div className="place-when__plot" style={grid} onMouseLeave={() => setActive(null)}>
              {data.map((d) => {
                const h = top > 0 ? (d.n / top) * 100 : 0;
                return (
                  <div
                    key={d.year}
                    className={`place-when__col${shown?.year === d.year ? " place-when__col--active" : ""}`}
                    tabIndex={0}
                    role="img"
                    aria-label={`${d.year}: ${speechCount(d.n)}`}
                    data-testid={`place-year-${d.year}`}
                    onMouseEnter={() => setActive(d)}
                    onFocus={() => setActive(d)}
                    onBlur={() => setActive(null)}
                    onClick={() => setActive(d)}
                  >
                    <div className="place-when__bar" style={{ height: `${h}%` }} />
                  </div>
                );
              })}
              <BarTip index={hovered ? data.indexOf(hovered) : -1} count={data.length} heightPct={hovered && top > 0 ? (hovered.n / top) * 100 : 0}>
                {readout}
              </BarTip>
            </div>
          </div>
          <div className="place-when__axis mono" style={grid} aria-hidden="true">
            {tickYears(data).map((y) => (
              <span key={y} className="place-when__tick" style={{ gridColumn: y - first + 1 }}>
                {y}
              </span>
            ))}
          </div>
        </div>

        <div className={showTable ? "place-when__table-wrap" : "sr-only"}>
          <table className="place-when__table">
            <caption>Speeches with this place tag, by year</caption>
            <thead>
              <tr>
                <th scope="col">Year</th>
                <th scope="col">Speeches about this place</th>
              </tr>
            </thead>
            <tbody>
              {data.map((d) => (
                <tr key={d.year}>
                  <td>{d.year}</td>
                  <td>{formatNumber(d.n)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {top < SMALL_MAX && (
          <p className="place-when__hint">
            The numbers are small. No year has {SMALL_MAX} speeches or more, so one speech can change a bar.
          </p>
        )}
        <p className="place-when__hint">
          Point at a year, or tap it, to read it.
        </p>
        <div>
          <Button variant="text" onClick={() => setShowTable((v) => !v)}>
            {showTable ? "Show as chart" : "Show as table"}
          </Button>
        </div>
      </div>
    </section>
  );
}

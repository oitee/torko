import React, { useState } from "react";
import Button from "../../components/Button.jsx";
import { formatNumber, shareOf } from "../../assets/js/format.js";
import "./HomeTrend.css";

// The share of each year: speeches with the tag, out of all speeches with a kept tag in that year.
// The number of tagged speeches changes from year to year, so a raw count would show the size of the year, not the subject.
// A year with no tagged speech has a share of 0.
export function yearShares(years) {
  const list = Array.isArray(years) ? years : [];
  return list
    .map((y) => {
      const n = Number(y.n) || 0;
      const tagged = Number(y.tagged) || 0;
      return { year: Number(y.year), n, tagged, rate: tagged > 0 ? n / tagged : 0 };
    })
    .filter((y) => !Number.isNaN(y.year))
    .sort((a, b) => a.year - b.year);
}

// HomeTrend shows when one subject rose and fell, as a bar for each year.
// The trend comes from /api/home/featured → trend.
export default function HomeTrend({ trend }) {
  const [showTable, setShowTable] = useState(false);
  const [active, setActive] = useState(null);

  if (!trend) return null;

  const data = yearShares(trend.years);
  if (data.length === 0) return null;

  const maxRate = Math.max(...data.map((d) => d.rate)) || 1;
  const first = data[0].year;
  const last = data[data.length - 1].year;
  const readout = active
    ? `${active.year} · ${shareOf(active.n, active.tagged)}`
    : "Point at a year for its share";

  return (
    <section className="home-feature" aria-labelledby="home-trend-title">
      <div className="home-feature__text">
        <h3 id="home-trend-title" className="home-feature__title">
          See when a subject rose and fell.
        </h3>
        <p className="home-feature__body">
          Each bar is one year. It shows the share of the tagged speeches of that year that carry the tag{" "}
          {trend.name}. A share does not grow when a year simply has more speeches.
        </p>
        <div className="home-feature__action">
          <Button variant="text" href={`/tag/${trend.slug}`}>
            See the tag {trend.name}
          </Button>
        </div>
      </div>

      <div className="home-trend">
        <div className="home-trend__head">
          <p className="home-trend__title">{trend.name} · share of tagged speeches, by year</p>
          <p className="home-trend__readout" aria-live="polite">
            {readout}
          </p>
        </div>

        <div className={showTable ? "sr-only" : "home-trend__visual"} aria-hidden={showTable ? "true" : undefined}>
          <div
            className="home-trend__plot"
            style={{ gridTemplateColumns: `repeat(${data.length}, minmax(0, 1fr))` }}
            onMouseLeave={() => setActive(null)}
          >
            {data.map((d) => (
              <div
                key={d.year}
                className={`home-trend__col${active?.year === d.year ? " home-trend__col--active" : ""}`}
                style={{ height: `${(d.rate / maxRate) * 100}%` }}
                tabIndex={0}
                role="img"
                aria-label={`${d.year}: ${shareOf(d.n, d.tagged)}`}
                data-testid={`trend-year-${d.year}`}
                onMouseEnter={() => setActive(d)}
                onFocus={() => setActive(d)}
                onBlur={() => setActive(null)}
              />
            ))}
          </div>
          <div className="home-trend__axis">
            <span>{first}</span>
            <span>{last}</span>
          </div>
        </div>

        <table className={showTable ? "home-trend__table" : "sr-only"}>
          <caption>{trend.name}: share of tagged speeches, by year</caption>
          <thead>
            <tr>
              <th scope="col">Year</th>
              <th scope="col">Share (speeches with the tag of all tagged speeches)</th>
            </tr>
          </thead>
          <tbody>
            {data.map((d) => (
              <tr key={d.year}>
                <td>{d.year}</td>
                <td>{shareOf(d.n, d.tagged)}</td>
              </tr>
            ))}
          </tbody>
        </table>

        <div className="home-trend__foot">
          {trend.total != null && (
            <p className="home-trend__total">
              {formatNumber(trend.total)} speeches carry the tag {trend.name} in all years.
            </p>
          )}
          <Button variant="text" onClick={() => setShowTable((v) => !v)}>
            {showTable ? "Show as chart" : "Show as table"}
          </Button>
        </div>
      </div>
    </section>
  );
}

export { HomeTrend };

import React, { useState } from "react";
import BarTip from "../../components/BarTip.jsx";
import Button from "../../components/Button.jsx";
import { formatNumber, shareOf } from "../../assets/js/format.js";
import { peakYear, yearSeries } from "../../assets/js/years.js";
import "./HomeTrend.css";

// HomeTrend shows when one subject rose and fell, as a bar for each year.
// The trend comes from /api/home/featured → trend.
export default function HomeTrend({ trend }) {
  const [showTable, setShowTable] = useState(false);
  const [active, setActive] = useState(null);

  if (!trend) return null;

  const data = yearSeries(trend.years);
  if (data.length === 0) return null;

  const maxRate = Math.max(...data.map((d) => d.rate)) || 1;
  const peak = peakYear(data, (d) => d.rate);
  const first = data[0].year;
  const last = data[data.length - 1].year;
  // One bar is green: the year under the pointer or the finger, else the highest year. Only the first has a pop-up.
  // The list of years is built again on each render, so the active year is found by its year, not by the object.
  const hovered = (active && data.find((d) => d.year === active.year)) || null;
  const shown = hovered || peak;
  const middle = Math.round((first + last) / 2);

  const pickAt = (event) => {
    const touch = event.touches?.[0];
    if (!touch) return;
    const box = event.currentTarget.getBoundingClientRect();
    const index = Math.floor(((touch.clientX - box.left) / box.width) * data.length);
    setActive(data[Math.min(data.length - 1, Math.max(0, index))]);
  };

  return (
    <section className="home-feature" aria-labelledby="home-trend-title">
      <div className="home-feature__text">
        <h3 id="home-trend-title" className="home-feature__title">
          See when a subject rose and fell
        </h3>
        <p className="home-feature__body">
          Each bar is one year. It shows the share of the tagged speeches of that year that carry the tag{" "}
          {trend.name}. A share does not grow when a year simply has more speeches.
        </p>
        <div className="home-feature__action">
          <Button variant="text" href={`/tag/${trend.slug}`} className="home-feature__stretch">
            Read the speeches tagged under {trend.name}
          </Button>
        </div>
      </div>

      <div className="home-trend">
        <div className="home-trend__head">
          <p className="home-trend__title">{trend.name} · share of tagged speeches, by year</p>
        </div>

        <div className={showTable ? "sr-only" : "home-trend__visual"} aria-hidden={showTable ? "true" : undefined}>
          <div
            className="home-trend__plot"
            style={{ gridTemplateColumns: `repeat(${data.length}, minmax(0, 1fr))` }}
            onMouseLeave={() => setActive(null)}
            onTouchStart={pickAt}
            onTouchMove={pickAt}
          >
            {data.map((d) => (
              <div
                key={d.year}
                className={`home-trend__col${shown?.year === d.year ? " home-trend__col--active" : ""}`}
                style={{ height: `${(d.rate / maxRate) * 100}%` }}
                tabIndex={0}
                role="img"
                aria-label={`${d.year}: ${shareOf(d.n, d.tagged)}`}
                data-testid={`trend-year-${d.year}`}
                onMouseEnter={() => setActive(d)}
                onFocus={() => setActive(d)}
                onBlur={() => setActive(null)}
                onClick={() => setActive(d)}
              />
            ))}
            <BarTip index={hovered ? data.indexOf(hovered) : -1} count={data.length} heightPct={hovered ? (hovered.rate / maxRate) * 100 : 0}>
              {hovered ? `${hovered.year} · ${shareOf(hovered.n, hovered.tagged)}` : null}
            </BarTip>
          </div>
          <div className="home-trend__axis">
            <span>{first}</span>
            {middle > first && middle < last && <span>{middle}</span>}
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

import React from "react";
import { Link } from "react-router-dom";
import { formatNumber } from "../../assets/js/format.js";
import { HEADLINE_MIN_TAGGED as THIN_YEAR, MAX_COMPARE, displayName, fmtShare, fmtUsual } from "./trendsData.js";

function yearHref(slug, year) {
  return `/search?tag=${slug}&date_from=${year}-01-01&date_to=${year}-12-31`;
}

// One subject of a year: the bar is its share in that year, and the thin mark is its usual share.
// A bar that is longer than the scale stops at the end of the track, and the text says so.
function SubjectBar({ subject, year, max, lead, slugs, onAdd }) {
  const cut = subject.share > max;
  const width = `${Math.min(100, (100 * subject.share) / max)}%`;
  const usual = `${Math.min(100, (100 * subject.typical) / max)}%`;
  const inCompare = slugs.includes(subject.slug);
  const name = displayName(subject.name);
  return (
    <li className={`year-strip__subject ${lead ? "year-strip__subject--lead" : ""}`}>
      <div className="year-strip__label">
        <Link to={yearHref(subject.slug, year)} className="year-strip__name">{name}</Link>
        <span className="year-strip__share">
          {fmtShare(subject.share)} <span className="year-strip__usual">usually {fmtUsual(subject.typical)}</span>
          {cut && <span className="year-strip__cut" title="The bar is longer than the scale of the full years, so it stops at the end of the track."> bar cut</span>}
        </span>
      </div>
      <div className="year-strip__track" aria-hidden="true">
        <span className="year-strip__fill" style={{ width }} />
        <span className="year-strip__mark" style={{ left: usual }} />
        {cut && <span className="year-strip__break" />}
      </div>
      <button
        type="button"
        className={`year-strip__add${inCompare ? " year-strip__add--in" : ""}`}
        disabled={inCompare || slugs.length >= MAX_COMPARE}
        aria-label={inCompare ? `${name} is in the comparison` : `Compare ${name}`}
        onClick={() => onAdd(subject.slug)}
      >
        {inCompare ? "In the chart" : "+ Compare"}
      </button>
    </li>
  );
}

// YearStrip lists the years, latest year first. Each year shows the subjects that stood out, as bars on one shared scale.
// lastDate is the last date of the data. The latest year is a part year when it is set.
export default function YearStrip({ years, slugs, onAdd, lastDate }) {
  // The scale comes from full years only. A thin year, such as a year that has only begun, can pass the scale and fills its bar.
  const full = years.filter((y) => y.tagged >= THIN_YEAR);
  const max = Math.max(...(full.length ? full : years).flatMap((y) => y.subjects.map((s) => s.share)), 1);
  const lastYear = years.length ? Math.max(...years.map((y) => y.year)) : null;
  const latestFirst = [...years].sort((a, b) => b.year - a.year);
  return (
    <ol className="year-strip">
      {latestFirst.map((y) => {
        const part = y.year === lastYear && Boolean(lastDate);
        return (
          <li key={y.year} className="year-strip__year" id={`year-${y.year}`}>
            <div className="year-strip__when">
              <span className="year-strip__number">{y.year}</span>
              <span className="year-strip__base">
                {formatNumber(y.tagged)} tagged speeches
                {part && <span className="year-strip__part"> Part year: 1 Jan to {lastDate} only</span>}
              </span>
            </div>
            {y.subjects.length === 0 ? (
              <p className="year-strip__none">No subject passes the rule in this year.</p>
            ) : (
              <ul className="year-strip__subjects">
                {y.subjects.map((s, i) => (
                  <SubjectBar key={s.slug} subject={s} year={y.year} max={max} lead={i === 0} slugs={slugs} onAdd={onAdd} />
                ))}
              </ul>
            )}
          </li>
        );
      })}
    </ol>
  );
}

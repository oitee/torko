import React from "react";
import { Link } from "react-router-dom";
import { HEADLINE_MIN_TAGGED as THIN_YEAR, MAX_COMPARE } from "./trendsData.js";

function yearHref(slug, year) {
  return `/search?tag=${slug}&date_from=${year}-01-01&date_to=${year}-12-31`;
}

// One subject of a year: the bar is its share in that year, and the thin mark is its usual share.
function SubjectBar({ subject, year, max, lead, slugs, onAdd }) {
  const width = `${Math.min(100, (100 * subject.share) / max)}%`;
  const usual = `${Math.min(100, (100 * subject.typical) / max)}%`;
  const inCompare = slugs.includes(subject.slug);
  return (
    <li className={`year-strip__subject ${lead ? "year-strip__subject--lead" : ""}`}>
      <div className="year-strip__label">
        <Link to={yearHref(subject.slug, year)} className="year-strip__name">{subject.name}</Link>
        <span className="year-strip__share">
          {subject.share}% <span className="year-strip__usual">usually {subject.typical}%</span>
        </span>
      </div>
      <div className="year-strip__track" aria-hidden="true">
        <span className="year-strip__fill" style={{ width }} />
        <span className="year-strip__mark" style={{ left: usual }} />
      </div>
      <button
        type="button"
        className="year-strip__add"
        disabled={inCompare || slugs.length >= MAX_COMPARE}
        aria-label={inCompare ? `${subject.name} is in the comparison` : `Compare ${subject.name}`}
        onClick={() => onAdd(subject.slug)}
      >
        {inCompare ? "In the chart" : "Compare"}
      </button>
    </li>
  );
}

// YearStrip lists the years, latest year first. Each year shows the subjects that stood out, as bars on one shared scale.
export default function YearStrip({ years, slugs, onAdd, lastDate }) {
  // The scale comes from full years only. A thin year, such as a year that has only begun, can pass the scale and fills its bar.
  const full = years.filter((y) => y.tagged >= THIN_YEAR);
  const max = Math.max(...(full.length ? full : years).flatMap((y) => y.subjects.map((s) => s.share)), 1);
  const lastYear = years.length ? Math.max(...years.map((y) => y.year)) : null;
  const latestFirst = [...years].sort((a, b) => b.year - a.year);
  return (
    <ol className="year-strip">
      {latestFirst.map((y) => (
        <li key={y.year} className="year-strip__year" id={`year-${y.year}`}>
          <div className="year-strip__when">
            <span className="year-strip__number">{y.year}</span>
            <span className="year-strip__base">
              {y.tagged.toLocaleString("en-IN")} tagged speeches{y.year === lastYear && lastDate ? `, to ${lastDate}` : ""}
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
      ))}
    </ol>
  );
}

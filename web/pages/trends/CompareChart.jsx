import React, { useState } from "react";
import { formatNumber } from "../../assets/js/format.js";
import { displayName, fmtShare, niceMax, yearRates } from "./trendsData.js";
import { spreadLabels } from "../../assets/js/spreadLabels.js";
import { useWidth } from "../../assets/js/useWidth.js";

// Lines differ by dash and by marker, not by hue. The palette keeps hue for other meanings.
const LINES = [
  { dash: "", marker: "circle", className: "trends-line--1" },
  { dash: "7 4", marker: "square", className: "trends-line--2" },
  { dash: "2 3", marker: "diamond", className: "trends-line--3" },
  { dash: "11 3 2 3", marker: "triangle", className: "trends-line--4" },
];
const PAD = { left: 44, right: 16, top: 26, bottom: 28 };
const LABELS_MIN_WIDTH = 520; // below this width the legend is the only key, because the end labels would crowd the plot

function Marker({ kind, x, y }) {
  if (kind === "circle") return <circle cx={x} cy={y} r={3} />;
  if (kind === "square") return <rect x={x - 3} y={y - 3} width={6} height={6} />;
  if (kind === "diamond") return <path d={`M${x} ${y - 4}L${x + 4} ${y}L${x} ${y + 4}L${x - 4} ${y}Z`} />;
  return <path d={`M${x} ${y - 4}L${x + 4} ${y + 3}L${x - 4} ${y + 3}Z`} />;
}

const short = (name, max) => (name.length > max ? `${name.slice(0, max - 1)}…` : name);

// The years that get a label on the x axis: the first, the last, and each fifth year.
// A fifth year that is 3 years or less from the first or the last year has no label, so two labels never touch.
export function yearLabels(years) {
  if (!years.length) return [];
  const first = years[0];
  const last = years[years.length - 1];
  const middle = years.filter((yr) => yr % 5 === 0 && yr - first > 3 && last - yr > 3);
  return [...new Set([first, ...middle, last])];
}

// One line for each subject, and a readout of the year under the pointer, the finger or the keyboard cursor.
// measure is "share" (percent of the tagged speeches of the year) or "count" (speeches).
// partial is { year, label } when the last year of the data is a part year. Its points are hollow.
export default function CompareChart({ series, measure = "share", title, partial = null }) {
  const [active, setActive] = useState(null);
  const [box, W] = useWidth(900);
  const H = W < 600 ? 280 : 340;
  const isCount = measure === "count";
  const names = series.map((s) => displayName(s.name));
  const lines = series.map((s) => yearRates(s.years).map((p) => ({ ...p, value: isCount ? p.n : p.rate })));
  const years = lines[0].map((p) => p.year);
  const top = niceMax(Math.max(...lines.flat().map((p) => p.value || 0)));
  const withLabels = W >= LABELS_MIN_WIDTH;
  const labelW = withLabels ? Math.round(Math.min(190, W * 0.26)) : 0;
  const right = PAD.right + labelW;
  const x = (i) => PAD.left + (i * (W - PAD.left - right)) / Math.max(1, years.length - 1);
  const y = (v) => H - PAD.bottom - (v / top) * (H - PAD.top - PAD.bottom);
  const label = yearLabels(years);
  const slot = (W - PAD.left - right) / Math.max(1, years.length - 1);
  const lastIndex = years.length - 1;
  const ends = lines.map((points) => y(points[lastIndex].value || 0));
  const endY = withLabels ? spreadLabels(ends, 16, PAD.top, H - PAD.bottom) : [];
  const nameMax = Math.max(10, Math.floor((labelW - 18) / 7));

  const pick = (event) => {
    const rect = event.currentTarget.getBoundingClientRect();
    const px = event.clientX - rect.left;
    setActive(Math.max(0, Math.min(lastIndex, Math.round((px - PAD.left) / slot))));
  };
  const onKeyDown = (event) => {
    const keys = { ArrowLeft: -1, ArrowRight: 1 };
    if (event.key in keys) {
      event.preventDefault();
      setActive((a) => Math.max(0, Math.min(lastIndex, (a === null ? lastIndex : a) + keys[event.key])));
    } else if (event.key === "Home") {
      event.preventDefault();
      setActive(0);
    } else if (event.key === "End") {
      event.preventDefault();
      setActive(lastIndex);
    } else if (event.key === "Escape") {
      setActive(null);
    }
  };
  const yAxisTitle = isCount ? "Speeches with the subject" : "% of tagged speeches";

  return (
    <figure className="trends-chart">
      {title && <figcaption className="trends-chart__title">{title}</figcaption>}
      <ul className="trends-chart__legend">
        {series.map((s, i) => (
          <li key={s.slug} className={`trends-chart__key ${LINES[i].className}`}>
            <svg width="36" height="10" aria-hidden="true">
              <line x1="0" y1="5" x2="36" y2="5" strokeDasharray={LINES[i].dash} className="trends-chart__line" />
            </svg>
            <span>{names[i]}</span>
          </li>
        ))}
      </ul>
      <div className="trends-chart__readout" style={{ "--lines": series.length + 1 }}>
        <p className="trends-chart__year">{active === null ? "Hover, tap or use the arrow keys to read a year." : years[active]}</p>
        {active !== null && lines.map((points, i) => {
          const p = points[active];
          return (
            <p key={series[i].slug} className="trends-chart__value">
              {names[i]}: {isCount ? `${formatNumber(p.n)} speeches` : p.rate === null ? "no tagged speeches" : `${fmtShare(p.rate)} (${formatNumber(p.n)} of ${formatNumber(p.tagged)} tagged speeches)`}
            </p>
          );
        })}
      </div>
      <div ref={box} className="trends-chart__box">
      <svg
        viewBox={`0 0 ${W} ${H}`}
        width={W}
        height={H}
        className="trends-chart__svg"
        role="img"
        tabIndex={0}
        aria-label={`Lines of the ${isCount ? "speech count" : "share"} of each subject by year. Use the arrow keys to read a year. The table has the same numbers.`}
        onPointerMove={pick}
        onPointerDown={pick}
        onPointerLeave={(e) => { if (e.pointerType === "mouse") setActive(null); }}
        onKeyDown={onKeyDown}
      >
        <text x={PAD.left} y={14} className="trends-chart__tick">{yAxisTitle}</text>
        {[0, 0.5, 1].map((f) => (
          <g key={f}>
            <line x1={PAD.left} x2={W - right} y1={y(top * f)} y2={y(top * f)} className="trends-chart__grid" />
            <text x={PAD.left - 6} y={y(top * f) + 4} textAnchor="end" className="trends-chart__tick">{isCount ? formatNumber(top * f) : `${+(top * f).toFixed(2)}%`}</text>
          </g>
        ))}
        {label.map((yr) => (
          <text key={yr} x={x(years.indexOf(yr))} y={H - 8} textAnchor="middle" className="trends-chart__tick">{yr}</text>
        ))}
        {active !== null && <line x1={x(active)} x2={x(active)} y1={PAD.top} y2={H - PAD.bottom} className="trends-chart__cursor" />}
        {lines.map((points, i) => (
          <g key={series[i].slug} className={LINES[i].className}>
            <polyline
              fill="none"
              strokeDasharray={LINES[i].dash}
              className="trends-chart__line"
              points={points.map((p, j) => `${x(j)},${y(p.value || 0)}`).join(" ")}
            />
            {partial && partial.year === years[lastIndex] && (
              <circle cx={x(lastIndex)} cy={ends[i]} r={4} className="trends-chart__hollow" />
            )}
            {active !== null && <g className="trends-chart__marker"><Marker kind={LINES[i].marker} x={x(active)} y={y(points[active].value || 0)} /></g>}
            {withLabels && (
              <text x={W - right + 10} y={endY[i] + 4} className="trends-chart__end">{short(names[i], nameMax)}</text>
            )}
          </g>
        ))}
      </svg>
      </div>
      {partial && partial.year === years[lastIndex] && (
        <p className="trends-chart__part">The hollow point is {partial.year}, a part year. It runs from 1 Jan to {partial.label} only.</p>
      )}
    </figure>
  );
}

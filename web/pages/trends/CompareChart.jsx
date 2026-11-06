import React, { useState } from "react";
import { formatNumber } from "../../assets/js/format.js";
import { niceMax, yearRates } from "./trendsData.js";
import { useWidth } from "./useWidth.js";

// Lines differ by dash and by marker, not by hue. The palette keeps hue for other meanings.
const LINES = [
  { dash: "", marker: "circle", className: "trends-line--1" },
  { dash: "7 4", marker: "square", className: "trends-line--2" },
  { dash: "2 3", marker: "diamond", className: "trends-line--3" },
  { dash: "11 3 2 3", marker: "triangle", className: "trends-line--4" },
];
const PAD = { left: 44, right: 16, top: 16, bottom: 28 };

function Marker({ kind, x, y }) {
  if (kind === "circle") return <circle cx={x} cy={y} r={3} />;
  if (kind === "square") return <rect x={x - 3} y={y - 3} width={6} height={6} />;
  if (kind === "diamond") return <path d={`M${x} ${y - 4}L${x + 4} ${y}L${x} ${y + 4}L${x - 4} ${y}Z`} />;
  return <path d={`M${x} ${y - 4}L${x + 4} ${y + 3}L${x - 4} ${y + 3}Z`} />;
}

// CompareChart draws one line for each subject, and a line of text for the year under the pointer.
// measure is "share" (percent of the tagged speeches of the year) or "count" (speeches).
export default function CompareChart({ series, measure = "share", title }) {
  const [active, setActive] = useState(null);
  // The drawing width is the real width of the box, so the text keeps its real size on a phone.
  const [box, W] = useWidth(900);
  const H = W < 600 ? 260 : 340;
  const isCount = measure === "count";
  const lines = series.map((s) => yearRates(s.years).map((p) => ({ ...p, value: isCount ? p.n : p.rate })));
  const years = lines[0].map((p) => p.year);
  const top = niceMax(Math.max(...lines.flat().map((p) => p.value || 0)));
  const x = (i) => PAD.left + (i * (W - PAD.left - PAD.right)) / Math.max(1, years.length - 1);
  const y = (v) => H - PAD.bottom - (v / top) * (H - PAD.top - PAD.bottom);
  const label = years.filter((yr, i) => i === 0 || i === years.length - 1 || yr % 5 === 0);
  const slot = (W - PAD.left - PAD.right) / Math.max(1, years.length - 1);

  return (
    <figure className="trends-chart">
      {title && <figcaption className="trends-chart__title">{title}</figcaption>}
      <ul className="trends-chart__legend">
        {series.map((s, i) => {
          const point = active === null ? null : lines[i][active];
          return (
            <li key={s.slug} className={`trends-chart__key ${LINES[i].className}`}>
              <svg width="36" height="10" aria-hidden="true">
                <line x1="0" y1="5" x2="36" y2="5" strokeDasharray={LINES[i].dash} className="trends-chart__line" />
              </svg>
              <span>{s.name}</span>
              {point && <span className="trends-chart__value">{point.rate === null ? "–" : `${point.rate.toFixed(1)}%`}, {formatNumber(point.n)} speeches</span>}
            </li>
          );
        })}
      </ul>
      <p className="trends-chart__year" aria-live="polite">{active === null ? "Point at a year for its numbers" : years[active]}</p>
      <div ref={box} className="trends-chart__box">
      <svg viewBox={`0 0 ${W} ${H}`} width={W} height={H} className="trends-chart__svg" role="img" aria-label={`Lines of the ${isCount ? "speech count" : "share"} of each subject by year. The table has the same numbers.`} onMouseLeave={() => setActive(null)}>
        {[0, 0.5, 1].map((f) => (
          <g key={f}>
            <line x1={PAD.left} x2={W - PAD.right} y1={y(top * f)} y2={y(top * f)} className="trends-chart__grid" />
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
            {active !== null && <g className="trends-chart__marker"><Marker kind={LINES[i].marker} x={x(active)} y={y(points[active].value || 0)} /></g>}
          </g>
        ))}
        {years.map((yr, j) => (
          <rect key={yr} x={x(j) - slot / 2} y={0} width={slot} height={H} fill="transparent" onMouseEnter={() => setActive(j)} />
        ))}
      </svg>
      </div>
    </figure>
  );
}

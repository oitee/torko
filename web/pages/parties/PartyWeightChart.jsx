import React, { useState } from "react";
import { Link } from "react-router-dom";
import { formatNumber, ordinal } from "../../assets/js/format.js";
import { spreadLabels } from "../trends/raceData.js";
import { useWidth } from "../trends/useWidth.js";

// A party with a colour token in tokens.css draws in that colour. The others draw in ink and differ by dash.
// Every line also has its name at its end, so colour is never the only cue.
const TOKEN = { BJP: "var(--party-bjp)", INC: "var(--party-inc)", AITC: "var(--party-aitc)", TDP: "var(--party-tdp)", BSP: "var(--party-bsp)" };
const DASHES = ["6 4", "2 4", "10 4 2 4", "4 4"];

// The style of each line, in the order of the series.
export function lineStyles(codes) {
  let d = 0;
  return codes.map((code) => (TOKEN[code] ? { stroke: TOKEN[code], dash: null } : { stroke: "var(--ink-2)", dash: DASHES[d++ % DASHES.length] }));
}

// The top of the y axis: the next half step above the largest weight, and at least 2.
export function weightTop(series) {
  const max = Math.max(2, ...series.flatMap((s) => s.points.map((p) => p.weight || 0)));
  return Math.ceil(max * 2) / 2;
}

const PAD = { left: 72, right: 8, top: 16, bottom: 30 };

// PartyWeightChart draws the speaking weight of each party in each term.
// 1 is the House: the members of the party spoke as often as the average member. 2 is twice as often.
export default function PartyWeightChart({ weights, names }) {
  const [box, W] = useWidth(800);
  const [active, setActive] = useState(null);
  const series = weights.series;
  const terms = weights.terms.map((t) => t.term);
  const H = W < 600 ? 300 : 340;
  const labelW = W < 600 ? 92 : 250;
  const plotRight = W - PAD.right - labelW;
  const top = weightTop(series);
  const x = (i) => PAD.left + (i / Math.max(1, terms.length - 1)) * (plotRight - PAD.left);
  const y = (v) => H - PAD.bottom - (v / top) * (H - PAD.top - PAD.bottom);
  const styles = lineStyles(series.map((s) => s.code));
  const ticks = [];
  for (let v = 0; v <= top + 1e-9; v += 0.5) ticks.push(v);
  // The name of each line sits at its last point. Names that would touch move apart.
  const ends = series.map((s) => {
    const last = [...s.points].reverse().find((p) => p.weight != null);
    return last ? y(last.weight) : y(1);
  });
  const labelY = spreadLabels(ends, 16, PAD.top, H - PAD.bottom);
  const label = (s) => (W < 600 ? s.code : names[s.code] || s.code);

  return (
    <div ref={box} className="party-weight">
      <svg viewBox={`0 0 ${W} ${H}`} width={W} height={H} className="party-weight__svg" role="img"
        aria-label="Lines of the speaking weight of six parties in each Lok Sabha. The table has the same numbers.">
        {ticks.map((v) => (
          <g key={v}>
            <line x1={PAD.left} x2={plotRight} y1={y(v)} y2={y(v)} className={v === 1 ? "party-weight__house" : "party-weight__grid"} />
            <text x={PAD.left - 6} y={y(v) + 4} textAnchor="end" className="party-weight__tick">{v === 0 ? "0" : v === 1 ? "1× House" : `${v}×`}</text>
          </g>
        ))}
        {terms.map((t, i) => (
          <text key={t} x={x(i)} y={H - 8} textAnchor="middle" className="party-weight__tick">{W < 600 ? String(t) : `${ordinal(t)} LS`}</text>
        ))}
        {active !== null && <line x1={x(active)} x2={x(active)} y1={PAD.top} y2={H - PAD.bottom} className="party-weight__cursor" />}
        {series.map((s, k) => {
          const pts = s.points.map((p, i) => (p.weight == null ? null : [x(i), y(p.weight)]));
          // A missing point breaks the line, so no line claims a value that the data does not have.
          const segments = [];
          let run = [];
          pts.forEach((p) => {
            if (p) run.push(p);
            else if (run.length) { segments.push(run); run = []; }
          });
          if (run.length) segments.push(run);
          return (
            <g key={s.code} style={{ color: styles[k].stroke }}>
              {segments.map((seg, j) => (
                <polyline key={j} points={seg.map((p) => p.join(",")).join(" ")} fill="none" stroke="currentColor" strokeWidth="2"
                  strokeDasharray={styles[k].dash || undefined} />
              ))}
              {pts.map((p, i) => p && <circle key={i} cx={p[0]} cy={p[1]} r={active === i ? 4.5 : 3} fill="currentColor" />)}
              {/* A short sample of the line, with its dash, ties the name to its line. */}
              <line x1={plotRight + 8} x2={plotRight + 28} y1={labelY[k]} y2={labelY[k]} stroke="currentColor" strokeWidth="2"
                strokeDasharray={styles[k].dash || undefined} />
              <Link to={`/party/${encodeURIComponent(s.code)}`}>
                <text x={plotRight + 32} y={labelY[k] + 4} className="party-weight__label">{label(s)}</text>
              </Link>
            </g>
          );
        })}
        {/* Each term is one wide target. A pointer or a tap on it reads the term. */}
        {terms.map((t, i) => (
          <rect key={t} x={x(i) - (plotRight - PAD.left) / (2 * Math.max(1, terms.length - 1))} y={PAD.top}
            width={(plotRight - PAD.left) / Math.max(1, terms.length - 1)} height={H - PAD.top - PAD.bottom}
            fill="transparent" onPointerEnter={() => setActive(i)} onPointerDown={() => setActive(i)} />
        ))}
      </svg>
      <p className="party-weight__readout" aria-live="polite">
        {active === null
          ? "Point at a term, or tap it, to read its numbers."
          : `${ordinal(terms[active])} Lok Sabha: ` +
            series
              .map((s) => {
                const p = s.points[active];
                return p.weight == null ? `${s.code} too few members` : `${s.code} ${p.weight.toFixed(2)}× (${formatNumber(p.speeches)} speeches, ${formatNumber(p.members)} members)`;
              })
              .join(" · ")}
      </p>
    </div>
  );
}

// The same numbers as a table, for a screen reader and for a reader who wants exact values.
export function PartyWeightTable({ weights }) {
  const terms = weights.terms.map((t) => t.term);
  return (
    <div className="index-table-frame">
      <table className="index-table">
        <thead>
          <tr>
            <th scope="col">Party</th>
            {terms.map((t) => <th key={t} scope="col" className="index-table__num">{`${ordinal(t)} LS`}</th>)}
          </tr>
        </thead>
        <tbody>
          {weights.series.map((s) => (
            <tr key={s.code}>
              <th scope="row">{s.code}</th>
              {s.points.map((p) => (
                <td key={p.term} className="index-table__num mono" title={`${formatNumber(p.speeches)} speeches, ${formatNumber(p.members)} members`}>
                  {p.weight == null ? "–" : `${p.weight.toFixed(2)}×`}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

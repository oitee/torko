import React, { useState } from "react";
import { formatNumber, ordinal } from "../../assets/js/format.js";
import { spreadLabels } from "../../assets/js/spreadLabels.js";
import { useWidth } from "../../assets/js/useWidth.js";
import "./PartyWeightChart.css";

// The colour of each party in this chart. A colour follows the party, not its rank, so a party keeps its colour
// when the list changes. The six colours passed a check for colour blindness and contrast, in both themes.
// A party with no colour here takes the next spare colour.
const PARTY_COLOUR = { BJP: 1, INC: 2, "CPI(M)": 3, SP: 4, AITC: 5, BJD: 6 };
const SPARE = [7, 8];

export function colourSlots(codes) {
  let spare = 0;
  return codes.map((code) => PARTY_COLOUR[code] || SPARE[spare++ % SPARE.length]);
}

// The weight axis is a log scale: 0.5× and 2× are the same distance from 1×, because half as often and twice as often
// are the same size of difference. The axis always shows 0.5× to 2×, and more when the data needs it.
export function weightDomain(series) {
  const values = series.flatMap((s) => s.points.map((p) => p.weight).filter((v) => v != null && v > 0));
  const lo = Math.min(0.5, ...values.map((v) => v / 1.1));
  const hi = Math.max(2, ...values.map((v) => v * 1.1));
  return [lo, hi];
}

// The story of the chart in one sentence, by a fixed rule: in the last full term (the term before the newest one),
// the party that spoke most often for its size and the party that spoke least often.
export function storyOf(weights, names) {
  const terms = weights.terms.map((t) => t.term);
  if (terms.length < 2) return null;
  const term = terms[terms.length - 2];
  const i = terms.indexOf(term);
  const rows = weights.series
    .map((s) => ({ code: s.code, w: s.points[i]?.weight }))
    .filter((r) => r.w != null)
    .sort((a, b) => b.w - a.w);
  if (rows.length < 2) return null;
  const top = rows[0];
  const low = rows[rows.length - 1];
  const name = (c) => names[c] || c;
  return {
    term,
    text: `In the ${ordinal(term)} Lok Sabha, the last full term, a member of ${name(top.code)} spoke ${top.w.toFixed(1)} times as often as the average member. A member of ${name(low.code)} spoke ${low.w.toFixed(1)} times as often.`,
  };
}

// The next set of shown parties after a click on one name of the legend, as in Grafana:
// a plain click shows only that party, or all parties when it is the only one shown.
// A click with Ctrl or Cmd adds or removes that one party.
export function nextShown(shown, code, all, add) {
  if (add) {
    const next = new Set(shown);
    if (next.has(code)) next.delete(code);
    else next.add(code);
    return next.size ? next : new Set(all);
  }
  if (shown.size === 1 && shown.has(code)) return new Set(all);
  return new Set([code]);
}

const PAD = { left: 64, right: 8, top: 24, bottom: 30 };

// 1× is the House: the members of the party spoke as often as the average member. 2× is twice as often.
export default function PartyWeightChart({ weights, names }) {
  const [box, W] = useWidth(800);
  const series = weights.series;
  const codes = series.map((s) => s.code);
  const [shown, setShown] = useState(() => new Set(codes));
  const [hover, setHover] = useState(null);
  const [active, setActive] = useState(null);
  const terms = weights.terms.map((t) => t.term);
  const narrow = W < 600;
  const H = narrow ? 300 : 360;
  const labelW = narrow ? 70 : 220;
  const plotRight = W - PAD.right - labelW;
  const [lo, hi] = weightDomain(series);
  const x = (i) => PAD.left + (i / Math.max(1, terms.length - 1)) * (plotRight - PAD.left);
  const y = (v) => {
    const f = (Math.log2(v) - Math.log2(lo)) / (Math.log2(hi) - Math.log2(lo));
    return H - PAD.bottom - f * (H - PAD.top - PAD.bottom);
  };
  const ticks = [0.25, 0.5, 1, 2, 4].filter((v) => v >= lo && v <= hi);
  const slots = colourSlots(codes);
  const visible = series.map((s, k) => ({ s, k })).filter(({ s }) => shown.has(s.code));
  const ends = visible.map(({ s }) => {
    const last = [...s.points].reverse().find((p) => p.weight != null);
    return last ? y(last.weight) : y(1);
  });
  const labelY = spreadLabels(ends, 16, PAD.top, H - PAD.bottom);
  const label = (s) => (narrow ? s.code : names[s.code] || s.code);
  const story = storyOf(weights, names);
  // The legend shows the weight of each party in one term for all: the last full term of the sentence above.
  const legendTerm = story ? story.term : terms[terms.length - 1];
  const legendIndex = terms.indexOf(legendTerm);
  const onLegend = (code, e) => setShown(nextShown(shown, code, codes, e.ctrlKey || e.metaKey));

  return (
    <div className="party-weight">
      {story && <p className="party-weight__story">{story.text}</p>}
      <div ref={box} className="party-weight__plot">
        <svg viewBox={`0 0 ${W} ${H}`} width={W} height={H} className="party-weight__svg" role="img"
          aria-label="Lines of the speaking weight of each party in each Lok Sabha, on a log scale around 1 times the House. The table has the same numbers.">
          <rect x={PAD.left} y={PAD.top} width={plotRight - PAD.left} height={y(1) - PAD.top} className="party-weight__band party-weight__band--more" />
          <text x={PAD.left + 8} y={PAD.top + 16} className="party-weight__band-label">Speaks more than its size</text>
          <text x={PAD.left + 8} y={H - PAD.bottom - 8} className="party-weight__band-label">Speaks less than its size</text>
          {ticks.map((v) => (
            <g key={v}>
              <line x1={PAD.left} x2={plotRight} y1={y(v)} y2={y(v)} className={v === 1 ? "party-weight__house" : "party-weight__grid"} />
              <text x={PAD.left - 6} y={y(v) + 4} textAnchor="end" className={v === 1 ? "party-weight__tick party-weight__tick--house" : "party-weight__tick"}>
                {v === 1 ? "1× House" : `${v}×`}
              </text>
            </g>
          ))}
          {terms.map((t, i) => (
            <text key={t} x={x(i)} y={H - 8} textAnchor="middle" className="party-weight__tick">{narrow ? String(t) : `${ordinal(t)} LS`}</text>
          ))}
          {active !== null && <line x1={x(active)} x2={x(active)} y1={PAD.top} y2={H - PAD.bottom} className="party-weight__cursor" />}
          {visible.map(({ s, k }, j) => {
            const pts = s.points.map((p, i) => (p.weight == null ? null : [x(i), y(p.weight)]));
            // A missing point breaks the line, so no line claims a value that the data does not have.
            const segments = [];
            let run = [];
            pts.forEach((p) => {
              if (p) run.push(p);
              else if (run.length) {
                segments.push(run);
                run = [];
              }
            });
            if (run.length) segments.push(run);
            const faded = hover !== null && hover !== s.code;
            return (
              <g key={s.code} className={`party-weight__series party-weight__series--c${slots[k]}${faded ? " party-weight__series--faded" : ""}`}>
                {segments.map((seg, n) => (
                  <polyline key={n} points={seg.map((p) => p.join(",")).join(" ")} className="party-weight__line" />
                ))}
                {pts.map((p, i) => p && <circle key={i} cx={p[0]} cy={p[1]} r={active === i ? 5 : 3.5} className="party-weight__dot" />)}
                <text x={plotRight + 10} y={labelY[j] + 4} className="party-weight__label">{label(s)}</text>
              </g>
            );
          })}
          {terms.map((t, i) => {
            const half = (plotRight - PAD.left) / (2 * Math.max(1, terms.length - 1));
            return (
              <rect key={t} x={x(i) - half} y={PAD.top} width={2 * half} height={H - PAD.top - PAD.bottom}
                fill="transparent" onPointerEnter={() => setActive(i)} onPointerDown={() => setActive(i)} />
            );
          })}
        </svg>
      </div>
      <p className="party-weight__legend-note">Weight in the {ordinal(legendTerm)} Lok Sabha</p>
      <ul className="party-weight__legend" aria-label="Parties in the chart. Select one to show it alone. Ctrl or Cmd adds or removes one.">
        {series.map((s, k) => {
          const on = shown.has(s.code);
          const value = s.points[legendIndex]?.weight;
          return (
            <li key={s.code}>
              <button
                type="button"
                className={`party-weight__key party-weight__series--c${slots[k]}${on ? "" : " party-weight__key--off"}`}
                aria-pressed={on}
                onClick={(e) => onLegend(s.code, e)}
                onPointerEnter={() => setHover(s.code)}
                onPointerLeave={() => setHover(null)}
                onFocus={() => setHover(s.code)}
                onBlur={() => setHover(null)}
              >
                <span className="party-weight__swatch" aria-hidden="true" />
                <span className="party-weight__key-name">{names[s.code] || s.code}</span>
                <span className="party-weight__key-value">{value != null ? `${value.toFixed(2)}×` : "–"}</span>
              </button>
            </li>
          );
        })}
      </ul>
      <p className="party-weight__readout" aria-live="polite">
        {active === null
          ? "Point at a term, or tap it, to read its numbers. Select a party in the list to show it alone."
          : `${ordinal(terms[active])} Lok Sabha: ` +
            visible
              .map(({ s }) => {
                const p = s.points[active];
                return p.weight == null ? `${s.code}: too few members` : `${s.code} ${p.weight.toFixed(2)}× (${formatNumber(p.speeches)} speeches, ${formatNumber(p.members)} members)`;
              })
              .join(" · ")}
      </p>
    </div>
  );
}

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

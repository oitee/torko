import React, { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { formatNumber } from "../../assets/js/format.js";
import { useAnswer } from "../../assets/js/useApi.js";
import Button from "../../components/Button.jsx";
import { ErrorState, Loading } from "../../components/States.jsx";
import { niceMax } from "./trendsData.js";
import { aboveAt, monthName, rankAt, spreadLabels } from "./raceData.js";
import { useWidth } from "./useWidth.js";

const MS_PER_FRAME = 400; // one month of the race takes this time to play
const TRAIL = 60;         // the line view shows the last 60 months
const PAD = { left: 40, right: 4, top: 30, bottom: 28 };
const ROW = 34;           // the height of one bar row, in pixels

const fmt = (v) => `${v >= 0 ? "+" : "−"}${Math.abs(v).toFixed(1)}`;
const short = (name, max = 34) => (name.length > max ? `${name.slice(0, max - 1)}…` : name);

// The bar view: one bar for each subject of the top, in rank order. A bar moves to its new rank with a short slide.
function RaceBars({ rows }) {
  const top = Math.max(0.1, ...rows.map((r) => r.value));
  // The caption names the unit of the values, so the reader does not need the footer to read the chart.
  return (
    <div className="race-bars-box">
    <p className="race-bars__unit">Points above usual share</p>
    <div className="race-bars" style={{ height: `${rows.length * ROW}px` }}>
      {rows.map((r, rank) => (
        <div key={r.subject.name} className="race-bars__row" style={{ transform: `translateY(${rank * ROW}px)` }}>
          <Link className="race-bars__name" to={`/tag/${r.subject.slug}`} title={r.subject.name}>{short(r.subject.name)}</Link>
          <span className="race-bars__track">
            <span className="race-bars__fill" style={{ width: `${(100 * Math.max(0, r.value)) / top}%` }} />
            <span className="race-bars__value">{fmt(r.value)}</span>
          </span>
        </div>
      ))}
    </div>
    </div>
  );
}

// The line view: the last five years of each subject of the top, with its name at the head of its line.
// The drawing width is the real width of the box, so the text keeps its real size on a phone.
function RaceLines({ rows, data, t, yMax }) {
  const [box, W] = useWidth(900);
  const H = W < 600 ? 360 : 420;
  const labelW = Math.round(Math.min(250, Math.max(130, W * 0.4)));
  const nameMax = Math.max(12, Math.floor((labelW - 14) / 7) - 6);
  const plotRight = W - PAD.right - labelW;
  const x = (f) => PAD.left + ((f - (t - TRAIL)) / TRAIL) * (plotRight - PAD.left);
  const y = (v) => H - PAD.bottom - (Math.max(0, v) / yMax) * (H - PAD.top - PAD.bottom);
  const step = niceMax(yMax / 3);
  const ticks = [];
  for (let v = 0; v <= yMax; v += step) ticks.push(v);
  const years = [];
  for (let f = Math.ceil(t - TRAIL); f <= t; f++) {
    const everyOther = plotRight - PAD.left < 260;
    if (f >= 0 && data.months[f].endsWith("-01") && (!everyOther || Number(data.months[f].slice(0, 4)) % 2 === 0)) years.push(f);
  }
  const heads = rows.map((r) => y(r.value));
  const labels = spreadLabels(heads, 15, PAD.top + 4, H - PAD.bottom);
  return (
    <div ref={box} className="race-lines-box">
    <svg viewBox={`0 0 ${W} ${H}`} width={W} height={H} className="race-lines" role="img" aria-label="Lines of the subjects of the top over the last five years">
      <text x={PAD.left} y={14} className="trends-chart__tick">Points above usual share</text>
      {ticks.map((v) => (
        <g key={v}>
          <line x1={PAD.left} x2={plotRight} y1={y(v)} y2={y(v)} className="trends-chart__grid" />
          <text x={PAD.left - 6} y={y(v) + 4} textAnchor="end" className="trends-chart__tick">{v === 0 ? "0" : `+${+v.toFixed(2)}`}</text>
        </g>
      ))}
      {years.map((f) => (
        <text key={f} x={x(f)} y={H - 8} textAnchor="middle" className="trends-chart__tick">{data.months[f].slice(0, 4)}</text>
      ))}
      {rows.map((r, rank) => {
        const pts = [];
        for (let f = Math.max(0, Math.ceil(t - TRAIL)); f <= Math.floor(t); f++) pts.push(`${x(f)},${y(aboveAt(r.subject, data.tagged, f))}`);
        pts.push(`${x(t)},${heads[rank]}`);
        const cls = rank < 3 ? "race-lines__line race-lines__line--lead" : "race-lines__line";
        return (
          <g key={r.subject.name} className={cls}>
            <polyline points={pts.join(" ")} />
            <circle cx={x(t)} cy={heads[rank]} r={3} />
            <line x1={x(t) + 4} y1={heads[rank]} x2={plotRight + 10} y2={labels[rank]} className="race-lines__leader" />
            <text x={plotRight + 14} y={labels[rank] + 4} className="race-lines__label">
              {short(r.subject.name, nameMax)} <tspan className="race-lines__value">{fmt(r.value)}</tspan>
            </text>
          </g>
        );
      })}
    </svg>
    </div>
  );
}

// TopicRace plays the months from 2000 to now. Each frame ranks the subjects by how far their share of the last 12 months
// is above their typical share. view is "bars" or "lines".
export default function TopicRace() {
  const { data, loading, error, retry } = useAnswer("/api/trends/race");
  const [t, setT] = useState(null);
  const [playing, setPlaying] = useState(false);
  const [view, setView] = useState("bars");
  const yMaxRef = useRef(null);
  const last = data ? data.months.length - 1 : 0;

  useEffect(() => {
    if (data && t === null) setT(last);
  }, [data, t, last]);

  useEffect(() => {
    if (!playing) return undefined;
    let frame;
    let before = performance.now();
    const tick = (now) => {
      const dt = Math.min(100, now - before); // a hidden tab gets no frames, so the race must not jump when the tab comes back
      before = now;
      setT((v) => {
        const next = v + dt / MS_PER_FRAME;
        if (next >= last) {
          setPlaying(false);
          return last;
        }
        return next;
      });
      frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [playing, last]);

  if (loading && !data) return <Loading lines={6} />;
  if (error) return <ErrorState error={error} onRetry={retry} />;
  if (!data || t === null) return null;

  const { rules } = data;
  const rows = rankAt(data.subjects, data.tagged, t, rules.top, rules.min_window_speeches);
  const near = Math.round(t);

  // The top of the line view moves slowly toward the largest value on screen, so the scale does not jump.
  let target = 0.5;
  for (const r of rows) {
    for (let f = Math.max(0, Math.ceil(t - TRAIL)); f <= near; f++) target = Math.max(target, aboveAt(r.subject, data.tagged, f));
  }
  target *= 1.08;
  yMaxRef.current = yMaxRef.current === null || !playing ? target : yMaxRef.current + (target - yMaxRef.current) * 0.08;

  const play = () => {
    if (t >= last) setT(0);
    setPlaying(true);
  };

  return (
    <div className="race">
      <div className="race__controls">
        <Button variant="primary" onClick={playing ? () => setPlaying(false) : play}>{playing ? "Pause" : t >= last ? "Play from 2000" : "Play"}</Button>
        <input
          type="range"
          className="race__slider"
          min={0}
          max={last}
          step={1}
          value={near}
          aria-label="Month of the race"
          aria-valuetext={monthName(data.months[near])}
          onChange={(e) => { setPlaying(false); setT(Number(e.target.value)); }}
        />
        <div className="trends-measure" role="group" aria-label="View of the race">
          {[["bars", "Bars"], ["lines", "Lines"]].map(([v, l]) => (
            <button key={v} type="button" className="trends-measure__option" aria-pressed={view === v} onClick={() => setView(v)}>{l}</button>
          ))}
        </div>
      </div>
      <p className="race__when">
        <span className="race__month">{monthName(data.months[near])}</span>
      </p>
      {view === "bars" ? <RaceBars rows={rows} /> : <RaceLines rows={rows} data={data} t={t} yMax={yMaxRef.current} />}
      {!playing && (
        <ol className="sr-only">
          {rows.map((r) => (
            <li key={r.subject.name}>{r.subject.name}: {r.share.toFixed(1)}% of tagged speeches, {fmt(r.value)} points above usual, {formatNumber(r.n)} speeches</li>
          ))}
        </ol>
      )}
    </div>
  );
}

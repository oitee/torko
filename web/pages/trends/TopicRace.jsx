import React, { useEffect, useMemo, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { formatNumber } from "../../assets/js/format.js";
import { useAnswer } from "../../assets/js/useApi.js";
import Button from "../../components/Button.jsx";
import CopyButton from "../../components/CopyButton.jsx";
import { ErrorState, Loading } from "../../components/States.jsx";
import { displayName, fmtShare, fmtUsual, niceMax } from "./trendsData.js";
import { aboveAt, monthName, rankAt, raceScale, spreadLabels } from "./raceData.js";
import MethodBlock from "./MethodBlock.jsx";
import { useWidth } from "./useWidth.js";

const MS_PER_FRAME = 900; // one month of the race takes this time to play
const TRAIL = 60;         // the line view shows the last 60 months

// The race has two views: bars and lines. Only the bars show now. Set this flag to true to show the switch to lines again.
export const SHOW_LINES_VIEW = false;
const PAD = { left: 40, right: 4, top: 30, bottom: 28 };

const fmt = (v) => `${v >= 0 ? "+" : "−"}${Math.abs(v).toFixed(1)}`;
const short = (name, max = 34) => (name.length > max ? `${name.slice(0, max - 1)}…` : name);
const axisLabel = (v) => (v === 0 ? "0" : `+${+v.toFixed(2)}`);

// The bar view: one bar for each subject of the top, in rank order. A bar moves to its new rank with a short slide.
// Every month uses the same scale, so a bar of one length means the same number of points in every month.
// Each row also shows the share of the window and the usual share, the same pair as the list of years.
function RaceBars({ rows, scale, tagged }) {
  const ticks = [];
  for (let v = 0; v <= scale.top + 1e-9; v += scale.step) ticks.push(v);
  const at = (v) => `${(100 * v) / scale.top}%`;
  return (
    <div className="race-bars-box" style={{ "--rows": rows.length }}>
      <div className="race-bars">
        <div className="race-bars__grid" aria-hidden="true">
          {ticks.map((v) => <span key={v} className="race-bars__gridline" style={{ left: at(v) }} />)}
        </div>
        {rows.map((r, rank) => (
          <div
            key={r.subject.name}
            className="race-bars__row"
            style={{ "--rank": rank }}
            title={`${displayName(r.subject.name)}: ${formatNumber(r.n)} of ${formatNumber(tagged)} tagged speeches (${fmtShare(r.share)}), usually ${fmtUsual(r.subject.typical)}`}
          >
            <div className="race-bars__who">
              <Link className="race-bars__name" to={`/tag/${r.subject.slug}`}>{displayName(r.subject.name)}</Link>
              <span className="race-bars__meta">{fmtShare(r.share)}, usually {fmtUsual(r.subject.typical)}</span>
            </div>
            <span className="race-bars__track">
              <span className="race-bars__fill" style={{ width: `${Math.min(100, (100 * Math.max(0, r.value)) / scale.top)}%` }} />
              <span className="race-bars__value">{fmt(r.value)}</span>
            </span>
          </div>
        ))}
      </div>
      <div className="race-axis" aria-hidden="true">
        <div className="race-axis__area">
          {ticks.map((v) => <span key={v} className="race-axis__tick" style={{ left: at(v) }}>{axisLabel(v)}</span>)}
        </div>
      </div>
      <p className="race-bars__unit">Points above the usual share</p>
    </div>
  );
}

// The numbers of the month as a table: the same ten subjects as the bars.
function RaceTable({ rows, tagged, windowLabel }) {
  return (
    <div className="trends-table-wrap">
      <table className="trends-table">
        <caption className="trends-table__caption">{windowLabel}. Share is the speeches with the subject out of the {formatNumber(tagged)} tagged speeches of the window.</caption>
        <thead>
          <tr>
            <th scope="col">Rank</th>
            <th scope="col" className="trends-table__text">Subject</th>
            <th scope="col">Speeches</th>
            <th scope="col">Share</th>
            <th scope="col">Usual share</th>
            <th scope="col">Points above usual</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={r.subject.name}>
              <td className="trends-table__num">{i + 1}</td>
              <th scope="row" className="trends-table__text"><Link to={`/tag/${r.subject.slug}`}>{displayName(r.subject.name)}</Link></th>
              <td className="trends-table__num">{formatNumber(r.n)}</td>
              <td className="trends-table__num">{fmtShare(r.share)}</td>
              <td className="trends-table__num">{fmtUsual(r.subject.typical)}</td>
              <td className="trends-table__num">{fmt(r.value)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// The line view: the last five years of each subject of the top, with its name at the head of its line.
// The drawing width is the real width of the box, so the text keeps its real size on a phone.
function RaceLines({ rows, data, t, yMax }) {
  const navigate = useNavigate();
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
      <text x={PAD.left} y={14} className="trends-chart__tick">Points above the usual share</text>
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
            {/* The name opens the page of the subject, as the name of a bar does. */}
            <a
              href={`/tag/${r.subject.slug}`}
              className="race-lines__link"
              onClick={(e) => {
                e.preventDefault();
                navigate(`/tag/${r.subject.slug}`);
              }}
            >
              <text x={plotRight + 14} y={labels[rank] + 4} className="race-lines__label">
                {short(displayName(r.subject.name), nameMax)} <tspan className="race-lines__value">{fmt(r.value)}</tspan>
              </text>
            </a>
          </g>
        );
      })}
    </svg>
    </div>
  );
}

// TopicRace plays the months from 2000 to now. Each frame ranks the subjects by how far their share of the last 12 months
// is above their typical share. view is "bars" or "lines".
// month ("2020-03" or null for the latest) and view come from the address of the page, so a link keeps them.
// onChange({ month, view }) tells the page to write a new value. A value that is absent stays as it is.
export default function TopicRace({ month = null, view: askedView = "bars", onChange = () => {} }) {
  const view = SHOW_LINES_VIEW ? askedView : "bars";
  const { data, loading, error, retry } = useAnswer("/api/trends/race");
  const [t, setT] = useState(null);
  const [playing, setPlaying] = useState(false);
  const [showTable, setShowTable] = useState(false);
  const yMaxRef = useRef(null);
  const last = data ? data.months.length - 1 : 0;

  useEffect(() => {
    if (!data || t !== null) return;
    const i = month ? data.months.indexOf(month) : -1;
    setT(i >= 0 ? i : last);
  }, [data, t, last, month]);

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

  // One scale for the bars of every month. It depends on the data only.
  const scale = useMemo(
    () => (data ? raceScale(data.subjects, data.tagged, data.rules.min_window_speeches) : null),
    [data]
  );

  if (loading && !data) return <Loading lines={6} />;
  if (error) return <ErrorState error={error} onRetry={retry} />;
  if (!data || t === null) return null;

  const { rules } = data;
  const rows = rankAt(data.subjects, data.tagged, t, rules.top, rules.min_window_speeches);
  const near = Math.round(t);
  const label = data.months[near];
  const windowLabel = `${rules.window_months} months to ${monthName(label)}`;
  const monthParam = (i) => (i >= last ? null : data.months[i]);

  // The top of the line view moves slowly toward the largest value on screen, so the scale does not jump.
  let target = 0.5;
  for (const r of rows) {
    for (let f = Math.max(0, Math.ceil(t - TRAIL)); f <= near; f++) target = Math.max(target, aboveAt(r.subject, data.tagged, f));
  }
  target *= 1.08;
  yMaxRef.current = yMaxRef.current === null || !playing ? target : yMaxRef.current + (target - yMaxRef.current) * 0.08;

  const pause = () => {
    setPlaying(false);
    onChange({ month: monthParam(near) });
  };
  const play = () => {
    if (t >= last) setT(0);
    setPlaying(true);
  };
  const link = () => {
    const u = new URL(window.location.href);
    if (monthParam(near)) u.searchParams.set("month", monthParam(near));
    else u.searchParams.delete("month");
    if (view === "lines") u.searchParams.set("view", "lines");
    else u.searchParams.delete("view");
    return u.toString();
  };

  return (
    <div className="race">
      <div className="race__controls">
        <Button
          variant="primary"
          className="race__play"
          onClick={playing ? pause : play}
          aria-label={playing ? "Pause" : t >= last ? `Play from ${monthName(data.months[0])}` : "Play"}
        >
          {playing ? (
            <svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true"><rect x="3" y="2" width="3.5" height="12" fill="currentColor" /><rect x="9.5" y="2" width="3.5" height="12" fill="currentColor" /></svg>
          ) : (
            <svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true"><path d="M4 2 L14 8 L4 14 Z" fill="currentColor" /></svg>
          )}
        </Button>
        <input
          type="range"
          className="race__slider"
          min={0}
          max={last}
          step={1}
          value={near}
          aria-label="Month of the race"
          aria-valuetext={windowLabel}
          onChange={(e) => {
            const i = Number(e.target.value);
            setPlaying(false);
            setT(i);
            onChange({ month: monthParam(i) });
          }}
        />
        {SHOW_LINES_VIEW && (
          <div className="trends-measure" role="group" aria-label="View of the race">
            {[["bars", "Bars"], ["lines", "Lines"]].map(([v, l]) => (
              <button key={v} type="button" className="trends-measure__option" aria-pressed={view === v} onClick={() => onChange({ view: v === "bars" ? null : v })}>{l}</button>
            ))}
          </div>
        )}
      </div>
      <p className="race__when">
        <span className="race__month">{monthName(label)}</span>
      </p>
      {showTable ? (
        <RaceTable rows={rows} tagged={data.tagged[near]} windowLabel={windowLabel} />
      ) : view === "bars" ? (
        <RaceBars rows={rows} scale={scale} tagged={data.tagged[near]} />
      ) : (
        <RaceLines rows={rows} data={data} t={t} yMax={yMaxRef.current} />
      )}
      <div className="race__foot">
        <Button variant="text" onClick={() => setShowTable((v) => !v)} aria-pressed={showTable}>{showTable ? "Show as chart" : "Show as table"}</Button>
        <CopyButton text={link}>Copy link</CopyButton>
        <MethodBlock>
          <p>
            Each month shows the {rules.window_months} months up to it. Share = (the speeches with that subject) / (the total number of
            tagged speeches of those months). A speech is a tagged speech only if it has at least one subject label.
          </p>
          <p>Usual = the median share of the subject over all months. The bar is the share minus the usual share, in percentage points.</p>
          <p>
            A subject needs {formatNumber(rules.min_subject_speeches)} speeches over all years and {formatNumber(rules.min_window_speeches)} speeches
            in the window, to be considered.
          </p>
        </MethodBlock>
      </div>
      {!playing && !showTable && (
        <ol className="sr-only">
          {rows.map((r) => (
            <li key={r.subject.name}>{displayName(r.subject.name)}: {fmtShare(r.share)} of tagged speeches, {fmt(r.value)} points above usual, {formatNumber(r.n)} speeches</li>
          ))}
        </ol>
      )}
    </div>
  );
}

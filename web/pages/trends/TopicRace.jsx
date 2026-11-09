import React, { useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { formatNumber } from "../../assets/js/format.js";
import { prefersReducedMotion } from "../../assets/js/motion.js";
import { useAnswer } from "../../assets/js/useApi.js";
import Button from "../../components/Button.jsx";
import CopyButton from "../../components/CopyButton.jsx";
import { ErrorState, Loading } from "../../components/States.jsx";
import { displayName, fmtShare, fmtUsual } from "./trendsData.js";
import { monthName, rankAt, raceScale } from "./raceData.js";
import MethodBlock from "../../components/MethodBlock.jsx";

const MS_PER_FRAME = 900; // one month of the race takes this time to play
const AUTOPLAY_DELAY = 1200; // the race starts this long after the chart is in view
const fmt = (v) => `${v >= 0 ? "+" : "−"}${Math.abs(v).toFixed(1)}`;
const axisLabel = (v) => (v === 0 ? "0" : `+${+v.toFixed(2)}`);

// Every month uses the same scale, so a bar of one length means the same number of points in every month.
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
              <span
                className={r.value > scale.top ? "race-bars__fill race-bars__fill--cut" : "race-bars__fill"}
                style={{ width: `${Math.min(100, (100 * Math.max(0, r.value)) / scale.top)}%` }}
                title={r.value > scale.top ? "The bar is longer than the scale, so it stops at the end of the track." : undefined}
              />
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

// The years that get a tick under the timeline: each January of a year that ends in 0 or 5.
export function yearTicks(months) {
  return months
    .map((m, i) => ({ m, i }))
    .filter(({ m }) => m.endsWith("-01") && Number(m.slice(0, 4)) % 5 === 0)
    .map(({ m, i }) => ({ i, year: m.slice(0, 4) }));
}

// The race plays by itself only when nothing asks it not to: the reader set no month in the address,
// the system does not ask for reduced motion, and the browser can tell when the chart is in view.
export function canAutoplay(month) {
  if (month || typeof IntersectionObserver === "undefined") return false;
  return !prefersReducedMotion();
}

// TopicRace plays the months from 2000 to now. Each frame ranks the subjects by how far their share of the last 12 months
// is above their typical share. month ("2020-03", or null for the latest) comes from the address of the page.
export default function TopicRace({ month = null, onChange = () => {} }) {
  const { data, loading, error, retry } = useAnswer("/api/trends/race");
  const [t, setT] = useState(null);
  const [playing, setPlaying] = useState(false);
  const [showTable, setShowTable] = useState(false);
  const rootRef = useRef(null);
  // auto: the race may start by itself. It turns false for good after the first action of the reader.
  const auto = useRef(canAutoplay(month));
  const autoRun = useRef(false); // true while a run that started by itself plays
  const last = data ? data.months.length - 1 : 0;

  useEffect(() => {
    if (!data || t !== null) return;
    const i = month ? data.months.indexOf(month) : -1;
    // A race that will play by itself waits on its first month. Otherwise it shows the month asked for, or the latest.
    setT(auto.current ? 0 : i >= 0 ? i : last);
  }, [data, t, last, month]);

  // Start the race AUTOPLAY_DELAY after the chart comes into view. A run that started by itself pauses
  // when the chart leaves the view, so it does not play where nobody can see it.
  const ready = Boolean(data) && t !== null;
  useEffect(() => {
    if (!ready || !rootRef.current || typeof IntersectionObserver === "undefined") return undefined;
    let timer = null;
    const observer = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting) {
        if (auto.current && timer === null) {
          timer = setTimeout(() => {
            if (!auto.current) return;
            auto.current = false;
            autoRun.current = true;
            setPlaying(true);
          }, AUTOPLAY_DELAY);
        }
      } else {
        clearTimeout(timer);
        timer = null;
        if (autoRun.current) {
          autoRun.current = false;
          setPlaying(false);
        }
      }
    }, { threshold: 0.4 });
    observer.observe(rootRef.current);
    return () => {
      clearTimeout(timer);
      observer.disconnect();
    };
  }, [ready]);

  // Any action of the reader ends the automatic start for good.
  const touch = () => {
    auto.current = false;
    autoRun.current = false;
  };

  useEffect(() => {
    if (!playing) return undefined;
    let frame;
    let before = performance.now();
    const tick = (now) => {
      const dt = Math.min(100, now - before); // a hidden tab gets no frames, so the race must not jump when the tab comes back
      before = now;
      setT((v) => Math.min(last, v + dt / MS_PER_FRAME));
      frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [playing, last]);

  useEffect(() => {
    if (playing && t >= last) setPlaying(false);
  }, [playing, t, last]);

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

  const pause = () => {
    touch();
    setPlaying(false);
    onChange({ month: monthParam(near) });
  };
  const play = () => {
    touch();
    if (t >= last) setT(0);
    setPlaying(true);
  };
  const link = () => {
    const u = new URL(window.location.href);
    if (monthParam(near)) u.searchParams.set("month", monthParam(near));
    else u.searchParams.delete("month");
    return u.toString();
  };

  return (
    <div className="race" ref={rootRef}>
      <div className="race__panel">
      <div className="race__stage">
        {!showTable && <p className="race__month" aria-hidden="true">{monthName(label)}</p>}
        {showTable ? (
          <RaceTable rows={rows} tagged={data.tagged[near]} windowLabel={windowLabel} />
        ) : (
          <RaceBars rows={rows} scale={scale} tagged={data.tagged[near]} />
        )}
      </div>
      <div className="race__timeline">
        <button
          type="button"
          className="race__play"
          onClick={playing ? pause : play}
          aria-label={playing ? "Pause" : t >= last ? `Play from ${monthName(data.months[0])}` : "Play"}
        >
          {playing ? (
            <svg viewBox="0 0 12 12" width="12" height="12" aria-hidden="true"><rect x="2" y="1" width="2.5" height="10" fill="currentColor" /><rect x="7.5" y="1" width="2.5" height="10" fill="currentColor" /></svg>
          ) : (
            <svg viewBox="0 0 12 12" width="12" height="12" aria-hidden="true"><path d="M2.5 1 L11 6 L2.5 11 Z" fill="currentColor" /></svg>
          )}
        </button>
        <div className="race__track">
          <input
            type="range"
            className="race__slider"
            min={0}
            max={last}
            step={1}
            value={near}
            style={{ "--done": `${(100 * near) / Math.max(1, last)}%` }}
            aria-label="Month of the race"
            aria-valuetext={`${monthName(label)}. ${windowLabel}`}
            onChange={(e) => {
              const i = Number(e.target.value);
              touch();
              setPlaying(false);
              setT(i);
              onChange({ month: monthParam(i) });
            }}
          />
          <div className="race__ticks" aria-hidden="true">
            {yearTicks(data.months).map(({ i, year }) => (
              <span key={year} className="race__tick" style={{ left: `${(100 * i) / Math.max(1, last)}%` }}>{year}</span>
            ))}
          </div>
        </div>
      </div>
      </div>
      <div className="race__foot">
        <Button variant="text" onClick={() => { touch(); setPlaying(false); setShowTable((v) => !v); }} aria-pressed={showTable}>{showTable ? "Show as chart" : "Show as table"}</Button>
        <CopyButton text={link}>Copy link</CopyButton>
        <MethodBlock>
          <p>
            Each month shows the {rules.window_months} months up to it. Share = (the speeches with that subject) / (the total number of
            tagged speeches of those months). A speech is a tagged speech only if it has at least one subject label.
          </p>
          <p>Usual = the median share of the subject over all months. The bar is the share minus the usual share, in percentage points. A bar longer than the scale ends in a cut.</p>
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

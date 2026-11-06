import React, { useEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { getJSON } from "../assets/js/api.js";
import { formatDateLong, formatNumber } from "../assets/js/format.js";
import { useAnswer, useApi } from "../assets/js/useApi.js";
import Breadcrumb from "../components/Breadcrumb.jsx";
import Button from "../components/Button.jsx";
import Chip from "../components/Chip.jsx";
import CopyButton from "../components/CopyButton.jsx";
import PageAnswer from "../components/PageAnswer.jsx";
import PageLayout from "../components/PageLayout.jsx";
import { ErrorState, Loading } from "../components/States.jsx";
import CompareChart from "./trends/CompareChart.jsx";
import CompareTable from "./trends/CompareTable.jsx";
import MethodBlock from "./trends/MethodBlock.jsx";
import TopicRace from "./trends/TopicRace.jsx";
import YearStrip from "./trends/YearStrip.jsx";
import { HEADLINE_MIN_TAGGED, MAX_COMPARE, addSlug, defaultCompare, displayName, headline, removeSlug, readSlugs } from "./trends/trendsData.js";
import "./trends.css";

// Hand-picked starting points for Compare. They only fill the chart. They do not rank anything.
const EXAMPLES = [
  { label: "Planning Commission and NITI Aayog", slugs: "planning-commission,niti-aayog" },
  { label: "POTA and national security", slugs: "pota,national-security-and-counter-terrorism" },
  { label: "WTO and Atmanirbhar Bharat", slugs: "world-trade-organisation-wto,atmanirbhar-bharat" },
];

// The box that finds a tag or place to compare.
function SubjectPicker({ onAdd, full }) {
  const [text, setText] = useState("");
  const [rows, setRows] = useState([]);
  useEffect(() => {
    const q = text.trim();
    if (q.length < 2) {
      setRows([]);
      return undefined;
    }
    const controller = new AbortController();
    const timer = setTimeout(() => {
      getJSON("/api/search", { q }, { signal: controller.signal })
        .then((d) => setRows((d.results || []).filter((r) => r.kind === "tag" || r.kind === "place").slice(0, 8)))
        .catch(() => {});
    }, 250);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [text]);
  return (
    <div className="trends-pick">
      <input
        className="trends-pick__input"
        aria-label="Find a subject to compare"
        placeholder={full ? `Remove a subject to add another (${MAX_COMPARE} at most)` : "Find a subject, for example Farmers"}
        disabled={full}
        value={text}
        onChange={(e) => setText(e.target.value)}
      />
      {rows.length > 0 && (
        <ul className="trends-pick__list">
          {rows.map((r) => (
            <li key={r.slug}>
              <button type="button" className="trends-pick__option" onClick={() => { onAdd(r.slug); setText(""); }}>
                <span>{r.name}</span>
                <span className="trends-pick__n">{formatNumber(r.n_speeches)}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

// The Trends page: which subjects stood out in each year, and a chart to compare subjects over the years.
// The address keeps the state: compare (subjects), measure, month and view of the race.
// A list "compare=" with no subject means the reader cleared the chart. No "compare" at all means the first, ruled choice.
export default function Trends() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [showTable, setShowTable] = useState(false);
  const [sheetOpen, setSheetOpen] = useState(false);
  const closeRef = useRef(null);
  const measure = searchParams.get("measure") === "count" ? "count" : "share";
  const raceMonth = searchParams.get("month");
  const raceView = searchParams.get("view") === "lines" ? "lines" : "bars";
  const { data, loading, error, retry } = useAnswer("/api/trends");
  const chosen = searchParams.has("compare");
  const fallback = !chosen && data ? defaultCompare(data.years) : { slugs: [], years: [] };
  const slugs = chosen ? readSlugs(searchParams.get("compare")) : fallback.slugs;
  const key = slugs.join(",");
  const series = useApi(key ? `compare:${key}` : null, (signal) =>
    Promise.all(slugs.map((s) => getJSON(`/api/trends/${encodeURIComponent(s)}`, undefined, { signal })))
  );

  useEffect(() => {
    document.title = "Trends · Torko";
  }, []);

  // The sheet on a phone closes with Escape, and its close button takes the focus when it opens.
  useEffect(() => {
    if (!sheetOpen) return undefined;
    closeRef.current?.focus();
    const onKey = (e) => { if (e.key === "Escape") setSheetOpen(false); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [sheetOpen]);

  // Write some values of the address. A null value removes the key. The page does not scroll.
  const patch = (values) => {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      Object.entries(values).forEach(([k, v]) => {
        if (v === null || v === undefined || v === "") next.delete(k);
        else next.set(k, v);
      });
      return next;
    }, { replace: true, preventScrollReset: true });
  };
  const setCompare = (list) => patch({ compare: list.length ? list.join(",") : "" });
  const setRace = ({ month, view }) => patch({ ...(month !== undefined ? { month } : {}), ...(view !== undefined ? { view } : {}) });
  const setMeasure = (v) => patch({ measure: v === "count" ? "count" : null });
  // A click in the list of years only adds the subject. The tray and the chart show it. The page does not scroll.
  const addFromTimeline = (slug) => setCompare(addSlug(slugs, slug));

  if (loading && !data) return <main className="trends-page"><h1 className="sr-only">Trends</h1><Loading lines={8} /></main>;
  if (error) return <main className="trends-page"><ErrorState error={error} onRetry={retry} /></main>;
  if (!data) return null;

  const top = headline(data.years);
  const answer = (
    <div className="trends-head">
      <PageAnswer>
        {top ? (
          <>
            In {top.year}, {top.phrase} tagged speeches in the Lok Sabha {top.phrase.startsWith("one") ? "was" : "were"} about{" "}
            <Link className="trends-head__subject" to={`/tag/${top.slug}`}>{displayName(top.name)}</Link>
            {top.n !== undefined && top.tagged ? <> <span className="trends-head__count">({formatNumber(top.n)} of {formatNumber(top.tagged)})</span></> : null}.
          </>
        ) : (
          "What the Lok Sabha talked about, year by year"
        )}
      </PageAnswer>
      <p className="trends-head__lede">
        Below: the subjects that rose furthest, month by month. Then the top subjects of each year. Then a chart to compare subjects.
        A tagged speech is a speech with at least one subject label.
      </p>
      <p className="trends-head__rule">
        The sentence shows the largest share that any subject had in one year. Years with fewer than {formatNumber(HEADLINE_MIN_TAGGED)} tagged speeches are left out.
      </p>
    </div>
  );

  const loaded = series.data && series.data.length === slugs.length ? series.data : [];
  const lastDateLong = formatDateLong(data.last_date);
  const lastYear = Number(String(data.last_date).slice(0, 4));
  const partial = String(data.last_date).slice(5) !== "12-31" ? { year: lastYear, label: lastDateLong } : null;
  const firstYear = loaded.length && loaded[0].years.length ? loaded[0].years[0].year : "";
  const chartTitle = `${measure === "count" ? "Speeches that carry each subject" : "Share of tagged speeches that carry each subject"}, by year. Lok Sabha, ${firstYear} to ${lastDateLong}. Source: torko.in`;
  const rules = data.rules || {};
  const names = loaded.map((t) => displayName(t.name));

  return (
    <PageLayout breadcrumb={<Breadcrumb items={[{ label: "Trends" }]} />} answer={answer}>
      <div className="trends-body">
        <section className="trends-race" aria-labelledby="trends-race-title">
          <div className="trends-race__head">
            <h2 id="trends-race-title" className="trends-section-title">The subjects rise and fall, month by month</h2>
          </div>
          <TopicRace month={raceMonth} view={raceView} onChange={setRace} />
        </section>

        <section className="trends-years" aria-labelledby="trends-years-title">
          <h2 id="trends-years-title" className="trends-section-title">The year’s subjects, latest year first</h2>
          <p className="trends-years__note">
            The bar is the subject’s share of the tagged speeches of the year. The thin mark is its usual share. A name opens its speeches of that year.
          </p>
          <MethodBlock full={data.counts_note}>
            <p>
              Each year lists the top {rules.subjects_per_year} subjects. A subject needs {formatNumber(rules.min_year_speeches)} speeches in the year and
              {" "}{formatNumber(rules.min_subject_speeches)} speeches over all years. Its share must be at least {rules.min_lift} times its usual share.
            </p>
            <p>
              Usual is the median of the yearly shares of the subject. A year counts by the date of the debate.
              Bars use one scale. The scale comes from years with at least {formatNumber(HEADLINE_MIN_TAGGED)} tagged speeches.
            </p>
          </MethodBlock>
          <YearStrip years={data.years} slugs={slugs} onAdd={addFromTimeline} lastDate={partial ? lastDateLong : ""} />
        </section>

        <section className={`trends-compare${sheetOpen ? " trends-compare--sheet" : ""}`} id="compare" aria-labelledby="trends-compare-title">
          <div className="trends-compare__head">
            <h2 id="trends-compare-title" className="trends-section-title">Compare subjects over the years</h2>
            <button type="button" ref={closeRef} className="trends-compare__close" onClick={() => setSheetOpen(false)}>Close</button>
          </div>
          <SubjectPicker onAdd={(s) => setCompare(addSlug(slugs, s))} full={slugs.length >= MAX_COMPARE} />
          {slugs.length === 0 ? (
            <div className="trends-compare__empty">
              <p>Choose a subject, add one from the list of years, or start from an example.</p>
              <div className="trends-compare__examples">
                {EXAMPLES.map((e) => (
                  <Button key={e.slugs} variant="secondary" onClick={() => setCompare(e.slugs.split(","))}>{e.label}</Button>
                ))}
              </div>
            </div>
          ) : series.error ? (
            <ErrorState error={series.error} onRetry={series.retry} />
          ) : loaded.length === 0 ? (
            <Loading lines={4} />
          ) : (
            <>
              {!chosen && fallback.years.length > 0 && (
                <p className="trends-compare__first">
                  Shown first: the leading subject of {fallback.years[0]}{fallback.years[1] ? ` and the leading subject of ${fallback.years[1]}` : ""}. Choose other subjects to replace them.
                </p>
              )}
              <div className="trends-compare__chips">
                {loaded.map((t) => (
                  <Chip key={t.slug} label={displayName(t.name)} href={`/tag/${t.slug}`} onRemove={() => setCompare(removeSlug(slugs, slugs[loaded.indexOf(t)]))} />
                ))}
                <Button variant="text" onClick={() => setCompare([])}>Clear all</Button>
              </div>
              <div className="trends-measure" role="group" aria-label="Measure of the chart">
                {[["share", "Share of tagged speeches"], ["count", "Number of speeches"]].map(([v, l]) => (
                  <button key={v} type="button" className="trends-measure__option" aria-pressed={measure === v} onClick={() => setMeasure(v)}>
                    {l}
                  </button>
                ))}
              </div>
              {showTable ? <CompareTable series={loaded} /> : <CompareChart series={loaded} measure={measure} title={chartTitle} partial={partial} />}
              <div className="trends-compare__foot">
                <Button variant="text" onClick={() => setShowTable((v) => !v)}>{showTable ? "Show as chart" : "Show as table"}</Button>
                <CopyButton text={() => window.location.href}>Copy link</CopyButton>
                <p className="trends-compare__note">
                  Each line is the percent of the tagged speeches of a year that carry the subject. A share does not grow when a year simply has more speeches. A count does, so use the share to compare one year with another.
                </p>
              </div>
            </>
          )}
        </section>
      </div>
      {slugs.length > 0 && !sheetOpen && (
        <div className="trends-tray" role="region" aria-label="Comparison">
          <p className="trends-tray__text">
            <span className="trends-tray__count">Compare ({slugs.length})</span>{" "}
            <span className="trends-tray__names">{names.length ? names.join(", ") : slugs.join(", ")}</span>
          </p>
          <Button variant="secondary" onClick={() => setSheetOpen(true)}>Open chart</Button>
        </div>
      )}
    </PageLayout>
  );
}

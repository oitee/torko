import React, { useEffect, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { getJSON } from "../assets/js/api.js";
import { formatDateLong, formatNumber } from "../assets/js/format.js";
import { useAnswer, useApi } from "../assets/js/useApi.js";
import Breadcrumb from "../components/Breadcrumb.jsx";
import Button from "../components/Button.jsx";
import Chip from "../components/Chip.jsx";
import PageAnswer from "../components/PageAnswer.jsx";
import PageLayout from "../components/PageLayout.jsx";
import { ErrorState, Loading } from "../components/States.jsx";
import CompareChart from "./trends/CompareChart.jsx";
import CompareTable from "./trends/CompareTable.jsx";
import InfoTip from "./trends/InfoTip.jsx";
import TopicRace from "./trends/TopicRace.jsx";
import YearStrip from "./trends/YearStrip.jsx";
import { MAX_COMPARE, addSlug, headline, removeSlug, readSlugs } from "./trends/trendsData.js";
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
export default function Trends() {
  const [searchParams, setSearchParams] = useSearchParams();
  const slugs = readSlugs(searchParams.get("compare"));
  const compareRef = useRef(null);
  const [showTable, setShowTable] = useState(false);
  const [measure, setMeasure] = useState("share");
  const { data, loading, error, retry } = useAnswer("/api/trends");
  const key = slugs.join(",");
  const series = useApi(key ? `compare:${key}` : null, (signal) =>
    Promise.all(slugs.map((s) => getJSON(`/api/trends/${encodeURIComponent(s)}`, undefined, { signal })))
  );

  useEffect(() => {
    document.title = "Trends · Torko";
  }, []);

  const setCompare = (list) => {
    const next = new URLSearchParams(searchParams);
    if (list.length) next.set("compare", list.join(","));
    else next.delete("compare");
    setSearchParams(next, { replace: true, preventScrollReset: true });
  };
  const addFromTimeline = (slug) => {
    setCompare(addSlug(slugs, slug));
    compareRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  };

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
            <span className="trends-head__subject">{top.name}</span>.
          </>
        ) : (
          "What the Lok Sabha talked about, year by year"
        )}
      </PageAnswer>
      <p className="trends-head__lede">
        Each year has its own subjects. A war, a law, a scheme or a crisis takes the floor for a year, and then the house moves on.
        Below, each year shows the subjects that rose furthest above their usual level.
      </p>
    </div>
  );

  const loaded = series.data && series.data.length === slugs.length ? series.data : [];

  return (
    <PageLayout breadcrumb={<Breadcrumb items={[{ label: "Trends" }]} />} answer={answer}>
      <div className="trends-body">
        <section className="trends-race" aria-labelledby="trends-race-title">
          <div className="trends-race__head">
            <h2 id="trends-race-title" className="trends-section-title">The subjects rise and fall, month by month</h2>
            <InfoTip label="How Torko counts">
              Each month covers the 12 months up to it. A value is how far the subject’s share of the tagged speeches is above its
              usual share, in percentage points. Usual is its median over all months. Similar tags can each take a place.
            </InfoTip>
          </div>
          <TopicRace />
        </section>

        <section className="trends-years" aria-labelledby="trends-years-title">
          <h2 id="trends-years-title" className="trends-section-title">The year’s subjects, latest year first</h2>
          <p className="trends-years__note">
            The bar is the subject’s share of the year. The thin mark is its usual share. A name opens its speeches of that year.
          </p>
          <YearStrip years={data.years} slugs={slugs} onAdd={addFromTimeline} lastDate={formatDateLong(data.last_date)} />
        </section>

        <section className="trends-compare" ref={compareRef} aria-labelledby="trends-compare-title">
          <h2 id="trends-compare-title" className="trends-section-title">Compare subjects over the years</h2>
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
              <div className="trends-compare__chips">
                {loaded.map((t) => (
                  <Chip key={t.slug} label={t.name} href={`/tag/${t.slug}`} onRemove={() => setCompare(removeSlug(slugs, slugs[loaded.indexOf(t)]))} />
                ))}
              </div>
              <div className="trends-measure" role="group" aria-label="Measure of the chart">
                {[["share", "Share of the year"], ["count", "Number of speeches"]].map(([v, l]) => (
                  <button key={v} type="button" className="trends-measure__option" aria-pressed={measure === v} onClick={() => setMeasure(v)}>
                    {l}
                  </button>
                ))}
              </div>
              {showTable ? <CompareTable series={loaded} /> : <CompareChart series={loaded} measure={measure} />}
              <div className="trends-compare__foot">
                <Button variant="text" onClick={() => setShowTable((v) => !v)}>{showTable ? "Show the chart" : "Show the table"}</Button>
                <p className="trends-compare__note">
                  Each line is the percent of the tagged speeches of a year that carry the subject. A share does not grow when a year simply has more speeches. A count does, so use the share to compare one year with another.
                </p>
              </div>
            </>
          )}
        </section>
      </div>
    </PageLayout>
  );
}

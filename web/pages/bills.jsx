import React, { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAnswer } from "../assets/js/useApi.js";
import { TERM_SPANS, formatNumber, termShort } from "../assets/js/format.js";
import { ErrorState, Loading } from "../components/States.jsx";
import { StanceBar, countText } from "./bill.jsx";
import "./bill.css";
import "./bills.css";

const PAGE = 50;
const NARROW = 640;
const TERMS = [13, 14, 15, 16, 17, 18];

// The words of a text in lower case, with no punctuation.
const wordsOf = (t) => String(t || "").toLowerCase().match(/[\p{L}\p{N}]+/gu) || [];

// The bills whose name and year hold every word of the query. The bills with most members come first.
export function matchBills(bills, query, limit = 8) {
  const want = wordsOf(query);
  if (!want.length) return [];
  return bills
    .filter((b) => {
      const have = wordsOf(`${b.name} ${b.year}`);
      return want.every((w) => have.some((h) => h.startsWith(w)));
    })
    .sort((a, b) => b.members - a.members)
    .slice(0, limit);
}

// The bills that pass the chart filter: all, Constitution amendments, or one tag (a position in tag_choices).
export function filterBills(bills, { amendment = false, tag = null, term = null } = {}) {
  return bills.filter(
    (b) => (!amendment || b.amendment) && (tag === null || b.tags.includes(tag)) && (term === null || b.term === term)
  );
}

// The share of the members who spoke against the bill, from 0 to 1.
export const againstShare = (b) => (b.members ? b.counts.against / b.members : 0);

// A date as a year with a fraction, for the x position.
function yearOf(date) {
  if (!date) return null;
  const [y, m, d] = date.split("-").map(Number);
  return y + ((m - 1) * 30.5 + d) / 366;
}

// True while the window is narrower than NARROW. It changes when the window changes size.
function useNarrow() {
  const query = `(max-width: ${NARROW - 1}px)`;
  const [narrow, setNarrow] = useState(() => typeof window !== "undefined" && !!window.matchMedia?.(query).matches);
  useEffect(() => {
    const m = window.matchMedia?.(query);
    if (!m) return undefined;
    const on = () => setNarrow(m.matches);
    m.addEventListener("change", on);
    return () => m.removeEventListener("change", on);
  }, [query]);
  return narrow;
}

const fullName = (b) => `${b.name}, ${b.year}`;

function BillFind({ bills }) {
  const [q, setQ] = useState("");
  const navigate = useNavigate();
  const found = useMemo(() => matchBills(bills, q), [bills, q]);
  const submit = (e) => {
    e.preventDefault();
    if (found.length) navigate(`/bill/${found[0].id}`);
  };
  return (
    <form className="bills-find" onSubmit={submit} role="search">
      <div className="bills-find__row">
        <input
          type="search"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Citizenship (Amendment) Bill"
          aria-label="Find a bill by name"
          className="bills-find__input"
        />
        <button type="submit" className="bills-find__button">Find a bill</button>
      </div>
      {q.trim() && (
        <ul className="bills-find__list">
          {found.length === 0 && <li className="bill-meta">No bill name has these words.</li>}
          {found.map((b) => (
            <li key={b.id}>
              <Link to={`/bill/${b.id}`}>{fullName(b)}</Link>
              <span className="bill-meta"> · {formatNumber(b.members)} members spoke</span>
            </li>
          ))}
        </ul>
      )}
    </form>
  );
}

// The dot chart: x is the first day of debate, y the share against, the area of a dot the number of members.
export function BillsChart({ bills, labels, minMembers, term = null, narrow = false }) {
  const navigate = useNavigate();
  const [hover, setHover] = useState(null);
  // On a phone the drawing is narrower, so that the text and the dots keep a readable size.
  const W = narrow ? 380 : 760, H = 340, L = 44, R = 12, T = 12, B = 300;
  const from = term ? TERM_SPANS[term][0] : 1999;
  const to = term ? TERM_SPANS[term][1] || 2027 : 2027;
  const x = (yr) => L + ((yr - from) / (to - from)) * (W - L - R);
  const y = (p) => B - p * (B - T);
  const shown = bills.filter((b) => b.members >= minMembers && b.first_date);
  const most = Math.max(1, ...shown.map((b) => b.members));
  const r = (m) => 2 + Math.sqrt(m / most) * (narrow ? 7 : 10);
  const labelled = new Set(labels);
  const bands = TERMS.filter((t) => !term || t === term);
  return (
    <div className="bills-chart">
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" aria-label="Bills by first day of debate and share of members against">
        {bands.map((t, i) => {
          const a = Math.max(from, TERM_SPANS[t][0]);
          const b = Math.min(to, TERM_SPANS[t][1] || 2027);
          return (
            <g key={t}>
              {i % 2 === 0 && <rect x={x(a)} y={T} width={x(b) - x(a)} height={B - T} className="bills-chart__band" />}
              <text x={x(a) + 4} y={B + 16} className="bills-chart__axis">{termShort(t)} · {TERM_SPANS[t][0]}</text>
            </g>
          );
        })}
        {[0, 0.25, 0.5, 0.75, 1].map((p) => (
          <g key={p}>
            <line x1={L} x2={W - R} y1={y(p)} y2={y(p)} className="bills-chart__grid" />
            <text x={L - 6} y={y(p) + 4} textAnchor="end" className="bills-chart__axis">{Math.round(p * 100)}%</text>
          </g>
        ))}
        <text x={L} y={B + 34} className="bills-chart__axis">Share of the members who spoke against the bill</text>
        {[...shown].sort((a, b) => b.members - a.members).map((b) => (
          <circle
            key={b.id}
            cx={x(yearOf(b.first_date))}
            cy={y(againstShare(b))}
            r={r(b.members)}
            className={`bills-chart__dot${labelled.has(b.id) ? " bills-chart__dot--named" : ""}${hover?.id === b.id ? " bills-chart__dot--on" : ""}`}
            tabIndex={0}
            role="link"
            aria-label={`${fullName(b)}: ${b.members} members, ${countText(b.counts)}`}
            onMouseEnter={() => setHover(b)}
            onMouseLeave={() => setHover(null)}
            onFocus={() => setHover(b)}
            onBlur={() => setHover(null)}
            onClick={() => navigate(`/bill/${b.id}`)}
            onKeyDown={(e) => e.key === "Enter" && navigate(`/bill/${b.id}`)}
          />
        ))}
        {shown.filter((b) => labelled.has(b.id)).map((b) => {
          const cx = x(yearOf(b.first_date));
          const end = cx > W / 2;
          return (
            <text key={b.id} x={end ? cx - r(b.members) - 4 : cx + r(b.members) + 4} y={y(againstShare(b)) + 4}
              textAnchor={end ? "end" : "start"} className="bills-chart__label">
              {b.name.length > (narrow ? 22 : 38) ? `${b.name.slice(0, narrow ? 20 : 36)}…` : b.name}, {b.year}
            </text>
          );
        })}
      </svg>
      {hover && (() => {
        // The pop-up sits on the dot, like the pop-up of the bar charts. Near an edge it lines up with that edge.
        const cx = x(yearOf(hover.first_date));
        const top = y(againstShare(hover)) - r(hover.members) - 6;
        const side = cx < W * 0.2 ? "start" : cx > W * 0.8 ? "end" : "middle";
        return (
          <div className={`bills-chart__pop bills-chart__pop--${side}`} role="status" aria-live="polite"
            style={{ left: `${(cx / W) * 100}%`, top: `${(top / H) * 100}%` }}>
            <strong>{fullName(hover)}</strong>
            <div>{formatNumber(hover.members)} members · {countText(hover.counts)}</div>
          </div>
        );
      })()}
      <p className="bill-meta">Point to a dot to see the bill. Select it to open the bill.</p>
    </div>
  );
}

function ShortList({ title, rule, ids, byId }) {
  return (
    <div className="bills-short">
      <h3 className="bills-short__title">{title}</h3>
      <p className="bill-meta">{rule}</p>
      {ids.map((id) => {
        const b = byId[id];
        return (
          <div key={id} className="bills-short__row">
            <Link to={`/bill/${id}`}>{fullName(b)}</Link>
            <StanceBar counts={b.counts} />
            <div className="bill-meta">{formatNumber(b.members)} members · {countText(b.counts)}</div>
          </div>
        );
      })}
    </div>
  );
}

const SORTS = {
  latest: { label: "Latest", fn: (a, b) => (b.last_date || "").localeCompare(a.last_date || "") },
  members: { label: "Most members", fn: (a, b) => b.members - a.members },
  against: { label: "Most against", fn: (a, b) => againstShare(b) - againstShare(a) || b.members - a.members },
  name: { label: "Name", fn: (a, b) => a.name.localeCompare(b.name) },
};

function Chip({ on, onClick, children }) {
  return (
    <button type="button" className={`bills-chip${on ? " bills-chip--on" : ""}`} aria-pressed={on} onClick={onClick}>
      {children}
    </button>
  );
}

function AllBills({ bills }) {
  const [term, setTerm] = useState(null);
  const [sort, setSort] = useState("latest");
  const [shown, setShown] = useState(PAGE);
  const list = useMemo(() => filterBills(bills, { term }).sort(SORTS[sort].fn), [bills, term, sort]);
  const most = Math.max(1, ...list.map((b) => b.members));
  return (
    <section className="bill-sec">
      <h2 className="bill-sec__title">All bills</h2>
      <div className="bills-chips">
        <Chip on={term === null} onClick={() => { setTerm(null); setShown(PAGE); }}>All terms</Chip>
        {TERMS.map((t) => (
          <Chip key={t} on={term === t} onClick={() => { setTerm(t); setShown(PAGE); }}>{termShort(t)}</Chip>
        ))}
        <label className="bills-sort bill-meta">
          Sort{" "}
          <select value={sort} onChange={(e) => setSort(e.target.value)}>
            {Object.entries(SORTS).map(([k, s]) => <option key={k} value={k}>{s.label}</option>)}
          </select>
        </label>
      </div>
      <p className="bill-meta">{formatNumber(list.length)} bills. The bar shows the members who spoke, by stance. Its length is the number of members.</p>
      <div className="bills-table">
        {list.slice(0, shown).map((b) => (
          <div key={b.id} className="bills-table__row">
            <div><Link to={`/bill/${b.id}`}>{fullName(b)}</Link> <span className="bill-meta">· {termShort(b.term)}</span></div>
            <StanceBar counts={b.counts} width={Math.max(3, Math.round((b.members / most) * 100))} />
            <div className="bill-meta bills-table__n">{formatNumber(b.members)}</div>
          </div>
        ))}
      </div>
      {shown < list.length && (
        <button type="button" className="bill-readall" onClick={() => setShown(shown + PAGE)}>
          Show the next {Math.min(PAGE, list.length - shown)} bills
        </button>
      )}
    </section>
  );
}

export default function Bills() {
  const { data, loading, error, retry } = useAnswer("/api/bills");
  const narrow = useNarrow();
  const [amendment, setAmendment] = useState(false);
  const [tag, setTag] = useState(null);
  const [chartTerm, setChartTerm] = useState(narrow ? 18 : null);

  useEffect(() => {
    document.title = "Bills · Torko";
  }, []);

  if (loading) return <main className="bills-page"><h1 className="sr-only">Bills</h1><Loading lines={6} /></main>;
  if (error) return <main className="bills-page"><ErrorState error={error} onRetry={retry} /></main>;
  if (!data) return null;

  const byId = Object.fromEntries(data.bills.map((b) => [b.id, b]));
  const t = data.totals;
  const chartBills = filterBills(data.bills, { amendment, tag, term: chartTerm });
  const inChart = chartBills.filter((b) => b.members >= data.chart_min_members).length;

  return (
    <main className="bills-page">
      <div className="bills-head">
        <h1 className="bill-head__title">What the Lok Sabha said about each bill</h1>
        <p className="bills-lead">
          For each bill, read what it does, which members spoke for it and against it, and each speech.
        </p>
        <BillFind bills={data.bills} />
        <div className="bill-figures bill-figures--four">
          <div><div className="bill-num">{formatNumber(t.bills)}</div><div className="bill-meta">bills with a debate</div></div>
          <div><div className="bill-num">{formatNumber(t.terms.length)}</div><div className="bill-meta">terms of the Lok Sabha</div></div>
          <div><div className="bill-num">{formatNumber(t.speeches)}</div><div className="bill-meta">speeches on these bills</div></div>
          <div><div className="bill-num">{formatNumber(t.members)}</div><div className="bill-meta">members spoke on a bill</div></div>
        </div>
      </div>

      <section className="bill-sec">
        <h2 className="bill-sec__title">Bills by opposition in the debate</h2>
        <p className="bill-meta">{data.rules.chart} A spoken stance is not a vote.</p>
        <div className="bills-chips">
          <Chip on={!amendment && tag === null} onClick={() => { setAmendment(false); setTag(null); }}>All bills</Chip>
          <Chip on={amendment} onClick={() => setAmendment(!amendment)}>Constitution amendments</Chip>
          <label className="bills-sort bill-meta">
            Subject{" "}
            <select value={tag ?? ""} onChange={(e) => setTag(e.target.value === "" ? null : Number(e.target.value))}>
              <option value="">Any subject</option>
              {data.tag_choices.map((c, i) => <option key={c.slug} value={i}>{c.name} ({c.bills})</option>)}
            </select>
          </label>
        </div>
        <div className="bills-chips">
          <Chip on={chartTerm === null} onClick={() => setChartTerm(null)}>All terms</Chip>
          {TERMS.map((x) => <Chip key={x} on={chartTerm === x} onClick={() => setChartTerm(x)}>{termShort(x)}</Chip>)}
        </div>
        <BillsChart bills={chartBills} labels={amendment || tag !== null ? [] : data.labels} minMembers={data.chart_min_members} term={chartTerm} narrow={narrow} />
        <p className="bill-meta">
          {formatNumber(inChart)} bills in the chart. Bills with fewer than {data.chart_min_members} members who spoke are not in the chart.
        </p>
      </section>

      <section className="bill-sec">
        <div className="bills-shorts">
          <ShortList title="Latest" rule={data.rules.latest} ids={data.lists.latest} byId={byId} />
          <ShortList title="Most members" rule={data.rules.most_members} ids={data.lists.most_members} byId={byId} />
          <ShortList title="Most opposed" rule={data.rules.most_opposed} ids={data.lists.most_opposed} byId={byId} />
        </div>
      </section>

      <AllBills bills={data.bills} />

      <p className="bill-meta bill-method">
        {data.rules.member} <Link to="/method">Read the method</Link>
      </p>
    </main>
  );
}

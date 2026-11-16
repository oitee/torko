import React, { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useAnswer } from "../assets/js/useApi.js";
import { formatDateLong, formatNumber, termLong } from "../assets/js/format.js";
import Breadcrumb from "../components/Breadcrumb.jsx";
import PageLayout from "../components/PageLayout.jsx";
import PartyLink from "../components/PartyLink.jsx";
import { ErrorState, Loading } from "../components/States.jsx";
import NotFound from "./not_found.jsx";
import "./bill.css";

export const STANCES = ["for", "against", "mixed", "unclear"];
export const STANCE_LABELS = { for: "for", against: "against", mixed: "mixed", unclear: "not clear" };

// The days of the debate as "16 to 17 April 2026", or one date.
export function dateRange(first, last) {
  if (!first) return "";
  if (!last || first === last) return formatDateLong(first);
  return `${formatDateLong(first)} to ${formatDateLong(last)}`;
}

// The counts of one row as text, for example "18 for, 1 against". A stance with no member is left out.
export function countText(counts) {
  return STANCES.filter((s) => counts[s]).map((s) => `${counts[s]} ${STANCE_LABELS[s]}`).join(", ");
}

// One bar in four parts. width is the share of the longest bar, in per cent.
export function StanceBar({ counts, width = 100, label }) {
  return (
    <div className="bill-bar" style={{ width: `${width}%` }} role="img" aria-label={label || countText(counts)}>
      {STANCES.map((s) =>
        counts[s] ? <span key={s} className={`bill-bar__part bill-stance--${s}`} style={{ flexGrow: counts[s] }} /> : null
      )}
    </div>
  );
}

function Section({ title, children, id }) {
  return (
    <section className="bill-sec" id={id}>
      <h2 className="bill-sec__title">{title}</h2>
      {children}
    </section>
  );
}

// A different bill of the same name in the term before or after. Each bill links to the other.
export function SameNameCallout({ bill }) {
  return (bill.same_name || []).map((o) => (
    <aside key={o.id} className="bill-callout">
      A different bill with the same name was debated in the {termLong(o.term)}. <Link to={`/bill/${o.id}`}>Read it here</Link>
    </aside>
  ));
}

export function BillMembers({ bill }) {
  const c = bill.member_counts;
  return (
    <Section title="Where the members stood">
      <p className="bill-meta">
        Stance of a member is derived from the text of their speech and not from voting records.
      </p>
      <StanceBar counts={c} />
      <div className="bill-figures bill-figures--four">
        {STANCES.map((s) => (
          <div key={s}>
            <div className="bill-num">{formatNumber(c[s])}</div>
            <div className="bill-meta"><span className={`bill-key bill-stance--${s}`} />{STANCE_LABELS[s]}</div>
          </div>
        ))}
      </div>
    </Section>
  );
}

export function BillParties({ bill }) {
  const rows = bill.parties || [];
  if (rows.length === 0) return null;
  const most = Math.max(...rows.map((p) => p.members));
  const others = rows.find((p) => p.party === "Others");
  return (
    <Section title="By party">
      <div className="bill-parties">
        {rows.map((p) => (
          <div className="bill-party" key={p.party}>
            <div className="bill-party__name">{p.party === "Others" ? "Others" : <PartyLink code={p.party} />}</div>
            <div><StanceBar counts={p.counts} width={Math.max(4, Math.round((p.members / most) * 100))} label={`${p.party}: ${countText(p.counts)}`} /></div>
            <div className="bill-party__counts">{countText(p.counts)}</div>
          </div>
        ))}
      </div>
      {others?.no_party > 0 && (
        <p className="bill-meta">
          {others.no_party === 1 ? "1 member has" : `${others.no_party} members have`} no party in the data and {others.no_party === 1 ? "is" : "are"} in Others.
        </p>
      )}
    </Section>
  );
}

// "9 members, 12 points", or "1 point" for a reason that only an unidentified member gave.
export function reasonCount(r) {
  const pts = `${formatNumber(r.points)} ${r.points === 1 ? "point" : "points"}`;
  if (!r.members) return pts;
  return `${formatNumber(r.members)} ${r.members === 1 ? "member" : "members"}, ${pts}`;
}

// One quote, with the member, the party, and a link to the speech. A heading names the point, when it has one.
function Quote({ q, heading }) {
  return (
    <li className="bill-quote">
      {heading && <span className="bill-quote__point">{heading}</span>}
      <q className="bill-quote__text">{q.quote}</q>
      <span className="bill-meta">
        {q.member_id ? <Link to={`/member/${q.member_id}`}>{q.member}</Link> : "A member who is not identified"}
        {q.party ? ` · ${q.party}` : ""} · <Link to={`/speech/${q.speech_id}`}>Read the speech</Link>
      </span>
    </li>
  );
}

// The last row of a side: the points that a single member supported. Each point shows its label and its first quote.
export function otherPointsCount(n) {
  return `${formatNumber(n)} ${n === 1 ? "point" : "points"}`;
}

function OtherPoints({ list }) {
  return (
    <li className="bill-reason bill-reason--others">
      <details>
        <summary className="bill-reason__head">
          <span className="bill-reason__label">Points supported by a single member</span>
          <span className="bill-reason__count">{otherPointsCount(list.length)}</span>
        </summary>
        <ul className="bill-reason__quotes">
          {list.map((r) => <Quote key={r.id} q={r.quotes[0]} heading={r.label} />)}
        </ul>
      </details>
    </li>
  );
}

// One reason: the label, a bar of the members who gave it, and the quotes, which open on a click.
function Reason({ reason, side, most }) {
  const width = Math.max(2, Math.round((Math.max(reason.members, 0) / most) * 100));
  return (
    <li className="bill-reason">
      <details>
        <summary className="bill-reason__head">
          <span className="bill-reason__label">{reason.label}</span>
          <span className="bill-reason__count">{reasonCount(reason)}</span>
          <span className={`bill-reason__bar bill-stance--${side}`} style={{ width: `${width}%` }} aria-hidden="true" />
        </summary>
        <ul className="bill-reason__quotes">
          {reason.quotes.map((q, i) => <Quote key={`${q.speech_id}-${i}`} q={q} />)}
        </ul>
      </details>
    </li>
  );
}

function ReasonSide({ side, list, others, top, most }) {
  const [all, setAll] = useState(false);
  if (!list.length) return null;
  const shown = all ? list : list.slice(0, top);
  const showOthers = others.length > 0 && shown.length === list.length;
  const title = side === "for" ? "Reasons for the bill" : "Reasons against the bill";
  return (
    <div className="bill-reason-side">
      <h3 className="bill-sample-group__title"><span className={`bill-key bill-stance--${side}`} />{title}</h3>
      <ol className="bill-reasons">
        {shown.map((r) => <Reason key={r.id} reason={r} side={side} most={most} />)}
        {showOthers && <OtherPoints list={others} />}
      </ol>
      {list.length > top && (
        <button type="button" className="bill-readall" onClick={() => setAll(!all)} aria-expanded={all}>
          {all ? `Show the first ${top} reasons` : `Show all ${formatNumber(list.length)} reasons`}
        </button>
      )}
    </div>
  );
}

export function BillReasons({ bill }) {
  const reasons = bill.reasons || {};
  const sides = ["for", "against"].filter((s) => (reasons[s] || []).length);
  if (!sides.length) return null;
  const most = Math.max(1, ...sides.flatMap((s) => reasons[s].map((r) => r.members)));
  const top = bill.top_reasons || 5;
  const others = bill.reason_others || {};
  return (
    <Section title="The reasons members gave" id="reasons">
      <div className="bill-sample-groups">
        {sides.map((s) => <ReasonSide key={s} side={s} list={reasons[s]} others={others[s] || []} top={top} most={most} />)}
      </div>
    </Section>
  );
}

// The link to the full list of speeches on the bill.
export function readAllText(n) {
  return n === 1 ? "Read the speech on this bill" : `Read all ${formatNumber(n)} speeches on this bill`;
}

function ReadAll({ bill }) {
  return <Link className="bill-readall" to={`/search?bill=${bill.id}&sort=oldest`}>{readAllText(bill.speeches)}</Link>;
}

// One speech card: the member, the party, the seat, the date, the summary, and a link. stanceLabel adds the stance.
function SpeechCard({ s, stanceLabel }) {
  return (
    <article className={`bill-sample bill-sample--${s.stance}`}>
      <div className="bill-sample__who">
        {s.member_id ? <Link to={`/member/${s.member_id}`}>{s.member}</Link> : s.printed}
        <span className="bill-meta"> · {[stanceLabel && `${STANCE_LABELS[s.stance][0].toUpperCase()}${STANCE_LABELS[s.stance].slice(1)}`,
          s.party, s.seat, s.date && formatDateLong(s.date)].filter(Boolean).join(" · ")}</span>
      </div>
      {s.summary && <p className="bill-sample__summary">{s.summary}</p>}
      <Link to={`/speech/${s.id}`}>Read the speech</Link>
    </article>
  );
}

// A bill with few members: every speech in the order of the debate, with its stance. No charts.
export function BillAllSpeeches({ bill }) {
  const list = bill.samples || [];
  if (!list.length) return null;
  return (
    <Section title={list.length === 1 ? "The speech" : "The speeches"} id="speeches">
      <p className="bill-meta">{bill.sample_rule}</p>
      <div className="bill-samples">
        {list.map((s) => <SpeechCard key={s.id} s={s} stanceLabel />)}
      </div>
    </Section>
  );
}

// The sample speeches in one group for each stance, in the order of SAMPLE_ORDER.
const SAMPLE_ORDER = ["for", "against", "mixed"];

export function BillSamples({ bill }) {
  const groups = SAMPLE_ORDER.map((st) => [st, (bill.samples || []).filter((s) => s.stance === st)]).filter(([, l]) => l.length);
  return (
    <Section title="Speeches" id="speeches">
      <div className="bill-sample-groups">
        {groups.map(([stance, list]) => (
          <div key={stance} className="bill-sample-group">
            <h3 className="bill-sample-group__title"><span className={`bill-key bill-stance--${stance}`} />{STANCE_LABELS[stance][0].toUpperCase() + STANCE_LABELS[stance].slice(1)}</h3>
            <div className="bill-samples">
              {list.map((s) => <SpeechCard key={s.id} s={s} />)}
            </div>
          </div>
        ))}
      </div>
      <ReadAll bill={bill} />
    </Section>
  );
}

export default function Bill() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { data: bill, loading, error, retry } = useAnswer(`/api/bill/${id}`);

  // A bill that the merge step folded into another bill has the address of the kept bill.
  useEffect(() => {
    if (bill && String(bill.id) !== String(id)) navigate(`/bill/${bill.id}`, { replace: true });
  }, [bill, id, navigate]);

  useEffect(() => {
    if (bill) document.title = `${bill.name}, ${bill.year} · Torko`;
    else if (error?.status === 404) document.title = "Page not found · Torko";
  }, [bill, error]);

  if (loading) {
    return (
      <main className="bill-page">
        <h1 className="sr-only">Bill</h1>
        <Loading lines={6} />
      </main>
    );
  }
  if (error?.status === 404) return <NotFound />;
  if (error) return <main className="bill-page"><ErrorState error={error} onRetry={retry} /></main>;
  if (!bill) return null;

  const title = `${bill.name}, ${bill.year}`;
  const head = (
    <div className="bill-head">
      <h1 className="bill-head__title">{title}</h1>
      <div className="bill-figures bill-figures--four">
        <div><div className="bill-num">{formatNumber(bill.debates.length)}</div><div className="bill-meta">{bill.debates.length === 1 ? "debate" : "debates"}</div></div>
        <div><div className="bill-num">{formatNumber(bill.speeches)}</div><div className="bill-meta">{bill.speeches === 1 ? "speech" : "speeches"}</div></div>
        <div><div className="bill-num">{formatNumber(bill.members)}</div><div className="bill-meta">{bill.members === 1 ? "member spoke" : "members spoke"}</div></div>
        <div><div className="bill-num">{formatNumber(bill.days)}</div><div className="bill-meta">{bill.days === 1 ? "day of debate" : "days of debate"}</div></div>
      </div>
      <p className="bill-meta">{[bill.terms.map(termLong).join(", "), dateRange(bill.first_date, bill.last_date)].filter(Boolean).join(" · ")}</p>
    </div>
  );

  return (
    <div className="bill-page">
      <PageLayout breadcrumb={<Breadcrumb items={[{ label: "Home", href: "/" }, { label: "Bills", href: "/bills" }, { label: title }]} />} answer={head}>
        <div className="bill-main">
          <SameNameCallout bill={bill} />
          {bill.summary && (
            <Section title="What the bill does">
              <p className="bill-summary">{bill.summary}</p>
              <p className="bill-meta">{bill.summary_note}</p>
            </Section>
          )}
          {bill.small ? (
            <BillAllSpeeches bill={bill} />
          ) : (
            <>
              {bill.members > 0 && <BillMembers bill={bill} />}
              <BillParties bill={bill} />
              <BillReasons bill={bill} />
              <BillSamples bill={bill} />
            </>
          )}
          <Section title="The debates">
            <ul className="bill-debates">
              {bill.debates.map((d) => (
                <li key={d.id}><Link to={`/debate/${d.id}`}>{d.title}</Link> <span className="bill-meta">· {d.date && formatDateLong(d.date)}</span></li>
              ))}
            </ul>
          </Section>
          {bill.together.length > 0 && (
            <Section title="Debated together with">
              <ul className="bill-together">
                {bill.together.map((t) => (
                  <li key={t.id}><Link to={`/bill/${t.id}`}>{t.name}, {t.year}</Link></li>
                ))}
              </ul>
            </Section>
          )}
        </div>
      </PageLayout>
    </div>
  );
}

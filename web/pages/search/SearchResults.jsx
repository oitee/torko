import React from "react";
import { Link } from "react-router-dom";
import { formatDateISO, formatNumber, scriptLang, termShort } from "../../assets/js/format.js";
import Button from "../../components/Button.jsx";
import SpeakerLine from "../../components/SpeakerLine.jsx";
import TLDR from "../../components/TLDR.jsx";
import { EmptyState, ErrorState, Loading } from "../../components/States.jsx";
import { SORTS, excerptParts, pageWindow, yearSpan } from "./searchParams.js";

// One speech that matches: when, which debate, who, and the words in their sentence.
export function SearchSpeechRow({ speech }) {
  const meta = [
    formatDateISO(speech.date),
    speech.term != null ? termShort(speech.term) : "",
    speech.kind_label || "",
  ].filter(Boolean);
  const { parts, cutStart, cutEnd } = excerptParts(speech.excerpt, speech.marks);

  return (
    <li className="search-row">
      <div className="search-row__meta">
        <span>{meta.join(" · ")}</span>
        {speech.words != null && <span className="search-row__words">{formatNumber(speech.words)} words</span>}
      </div>
      <Link to={`/speech/${speech.id}`} className="search-row__debate">
        {speech.debate || "Speech"}
      </Link>
      <SpeakerLine speech={speech} />
      {/* The TLDR says what the speech is about. The excerpt below it shows where the words occur. */}
      {speech.summary && (
        <div className="search-row__tldr">
          <TLDR text={speech.summary} />
        </div>
      )}
      {parts.length > 0 && (
        <p className="search-row__excerpt" lang={scriptLang(speech.excerpt)}>
          “{cutStart && "… "}
          {parts.map((p, i) => (p.mark ? <mark key={i}>{p.text}</mark> : <React.Fragment key={i}>{p.text}</React.Fragment>))}
          {cutEnd && " …"}”
        </p>
      )}
    </li>
  );
}

// One member who spoke the words: who, from where, how often, and when.
export function SearchMemberRow({ member, href }) {
  const where = [member.party, member.seat, (member.terms || []).map(termShort).join(", ")].filter(Boolean).join(" · ");
  return (
    <li className="search-member">
      <div className="search-member__who">
        <Link to={`/member/${member.id}`} className="search-member__name">
          {member.name}
        </Link>
        {where && <span className="search-member__where">{where}</span>}
        {member.most_on?.slug && (
          <span className="search-member__most">
            Most on{" "}
            <Link to={`/tag/${member.most_on.slug}`} className="search-member__tag">
              {member.most_on.name}
            </Link>
          </span>
        )}
      </div>
      <Link to={href} className="search-member__count" aria-label={`${formatNumber(member.n)} speeches by ${member.name}`}>
        {formatNumber(member.n)}
      </Link>
      <span className="search-member__span">{yearSpan(member.first, member.last)}</span>
    </li>
  );
}

// The page links: previous, numbered pages, next.
function Pager({ page, pages, pageHref }) {
  if (!pages || pages <= 1) return null;
  return (
    <nav className="search-pager" aria-label="Pages">
      {page > 1 ? (
        <Link to={pageHref(page - 1)} className="search-pager__step" rel="prev">← Previous</Link>
      ) : (
        <span className="search-pager__step search-pager__step--off" aria-hidden="true">← Previous</span>
      )}
      <ol className="search-pager__pages">
        {pageWindow(page, pages).map((p, i) =>
          p === null ? (
            <li key={`gap-${i}`} className="search-pager__gap" aria-hidden="true">…</li>
          ) : (
            <li key={p}>
              {p === page ? (
                <span className="search-pager__num search-pager__num--current" aria-current="page">{formatNumber(p)}</span>
              ) : (
                <Link to={pageHref(p)} className="search-pager__num" aria-label={`Page ${p}`}>{formatNumber(p)}</Link>
              )}
            </li>
          )
        )}
      </ol>
      {page < pages ? (
        <Link to={pageHref(page + 1)} className="search-pager__step" rel="next">Next →</Link>
      ) : (
        <span className="search-pager__step search-pager__step--off" aria-hidden="true">Next →</span>
      )}
    </nav>
  );
}

// SearchResults shows the toggle between speeches and members, the sort, the rows and the pages.
export default function SearchResults({
  view,
  sort,
  page,
  data,
  loading,
  error,
  onRetry,
  speechTotal,
  membersTotal,
  viewHref,
  pageHref,
  memberHref,
  onSort,
  hasFilters,
  onReset,
}) {
  const tabs = [
    { value: "speeches", label: "Speeches", n: speechTotal },
    { value: "members", label: "Members", n: membersTotal },
  ];

  let body;
  if (loading) {
    body = (
      <div className="search-results__loading">
        <Loading lines={6} />
        <p className="search-results__wait">A search for a common word can take ten seconds.</p>
      </div>
    );
  } else if (error) {
    body = <ErrorState error={error} onRetry={onRetry} />;
  } else {
    const rows = view === "members" ? data?.members || [] : data?.speeches || [];
    if (rows.length === 0) {
      body = (
        <div className="search-results__empty">
          <EmptyState>No speeches match. Try fewer words, or remove a filter.</EmptyState>
          {hasFilters && (
            <Button variant="secondary" onClick={onReset}>Reset filters</Button>
          )}
        </div>
      );
    } else {
      const perPage = data.per_page || 20;
      const total = view === "members" ? data.members_total : data.total;
      const pages = view === "members" ? Math.ceil((total || 0) / perPage) : data.pages;
      const start = (page - 1) * perPage + 1;
      const end = Math.min(page * perPage, total || 0);
      const noun = view === "members" ? "members" : "speeches";
      body = (
        <>
          <p className="search-results__range">
            {`${formatNumber(start)}–${formatNumber(end)} of ${formatNumber(total)} ${noun}`}
          </p>
          {view === "members" ? (
            <>
              <div className="search-member search-member--head" aria-hidden="true">
                <span>Member</span>
                <span className="search-member__count-head">Speeches</span>
                <span className="search-member__span-head">Years</span>
              </div>
              <ol className="search-results__list search-results__list--members">
                {rows.map((m) => (
                  <SearchMemberRow key={m.id} member={m} href={memberHref(m.id)} />
                ))}
              </ol>
            </>
          ) : (
            <ol className="search-results__list">
              {rows.map((s) => (
                <SearchSpeechRow key={s.id} speech={s} />
              ))}
            </ol>
          )}
          <Pager page={page} pages={pages} pageHref={pageHref} />
        </>
      );
    }
  }

  return (
    <section className="search-results" aria-labelledby="search-results-title" aria-busy={loading}>
      <h2 id="search-results-title" className="search-sr">Results</h2>
      <div className="search-results__bar">
        <nav className="search-tabs" aria-label="Show">
          {tabs.map((t) => (
            <Link
              key={t.value}
              to={viewHref(t.value)}
              className={`search-tabs__tab ${view === t.value ? "search-tabs__tab--on" : ""}`}
              aria-current={view === t.value ? "page" : undefined}
            >
              {t.label}
              {t.n != null && <span className="search-tabs__n">{formatNumber(t.n)}</span>}
            </Link>
          ))}
        </nav>
        <label className="search-sort">
          <span className="search-sort__label">Sort</span>
          <select className="search-sort__select" value={sort} onChange={(e) => onSort(e.target.value)}>
            {SORTS.map((s) => (
              <option key={s.value} value={s.value}>
                {view === "members" && s.value === "longest" ? "Most words first" : s.label}
              </option>
            ))}
          </select>
        </label>
      </div>
      {body}
    </section>
  );
}

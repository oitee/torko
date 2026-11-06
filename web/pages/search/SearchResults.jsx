import React from "react";
import { Link } from "react-router-dom";
import { formatDateISO, formatNumber, scriptLang, termShort } from "../../assets/js/format.js";
import Button from "../../components/Button.jsx";
import SpeakerLine from "../../components/SpeakerLine.jsx";
import TLDR from "../../components/TLDR.jsx";
import { EmptyState, ErrorState, Loading } from "../../components/States.jsx";
import { MEMBER_ONLY_SORTS, SORTS, defaultSort, excerptParts, isPhrase, pageWindow, yearSpan } from "./searchParams.js";
import PartyLink from "../../components/PartyLink.jsx";

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
      {speech.match === "meaning" && (
        <p className="search-row__why">The summary is near your search in meaning. The speech does not use all your words.</p>
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
  const where = [member.seat, (member.terms || []).map(termShort).join(", ")].filter(Boolean).join(" · ");
  return (
    <li className="search-member">
      <div className="search-member__who">
        <Link to={`/member/${member.id}`} className="search-member__name">
          {member.name}
        </Link>
        {(member.party || where) && (
          <span className="search-member__where">
            <PartyLink code={member.party} />
            {member.party && where && " · "}
            {where}
          </span>
        )}
        {member.tag_counts && (
          <span className="search-member__most">
            {member.tag_counts.map((t, i) => (
              <React.Fragment key={t.slug}>
                {i > 0 && " · "}
                <Link to={`/search?member=${member.id}&tag=${t.slug}`} className="search-member__tag">
                  {t.name}: {formatNumber(t.n)}
                </Link>
              </React.Fragment>
            ))}
          </span>
        )}
        {member.most_on?.slug && (
          <span className="search-member__most">
            Most on{" "}
            <Link to={`/tag/${member.most_on.slug}`} className="search-member__tag">
              {member.most_on.name}
            </Link>
          </span>
        )}
      </div>
      {member.tag_counts ? (
        <span className="search-member__count">{formatNumber(member.n)}</span>
      ) : (
        <Link to={href} className="search-member__count" aria-label={`${formatNumber(member.n)} speeches by ${member.name}`}>
          {formatNumber(member.n)}
        </Link>
      )}
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

// The rule of the list in plain words, so that a reader knows why a speech is here.
function SearchRule({ query, sort, view, data }) {
  if (isPhrase(query)) return <p className="search-results__rule">These speeches hold these exact words in this order.</p>;
  if (data.by_meaning === false) {
    return <p className="search-results__rule">Search by meaning is not available now. These speeches hold all your words.</p>;
  }
  const shortened = view === "speeches" && sort === "best" && data.pages * data.per_page < data.total;
  return (
    <p className="search-results__rule">
      A speech is here when it holds all your words or its one-sentence summary is near your search in meaning.
      Put text in quote marks for an exact phrase.
      {shortened && " Best match orders the top of the list. Choose Latest first to read all of it."}
    </p>
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
  query,
  tagCount = 0,
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
        <p className="search-results__wait">A new search can take a few seconds.</p>
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
            {SORTS.filter(
              (s) => (s.value !== "best" || defaultSort(query) === "best") && (!MEMBER_ONLY_SORTS.includes(s.value) || view === "members")
            ).map((s) => (
              <option key={s.value} value={s.value}>
                {view === "members" && s.value === "longest" ? "Most words first" : s.label}
              </option>
            ))}
          </select>
        </label>
      </div>
      {tagCount > 1 && (
        <p className="search-results__rule">
          {view === "members"
            ? "Each member here raised each tag, in one speech or in different speeches. The numbers count the speeches for each tag."
            : "Each speech here carries all these tags. The Members view also lists a member who raised them in different speeches."}
        </p>
      )}
      {query && data && !loading && <SearchRule query={query} sort={sort} view={view} data={data} />}
      {body}
    </section>
  );
}

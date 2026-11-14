import React, { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useAnswer } from "../assets/js/useApi.js";
import { formatNumber, ordinal, termLong } from "../assets/js/format.js";
import Button from "../components/Button.jsx";
import Chip from "../components/Chip.jsx";
import PageLayout from "../components/PageLayout.jsx";
import { ErrorState, Loading } from "../components/States.jsx";
import { LIFT_MORE, LIFT_MUCH, PartyCards, PartyGrid, PartyHouse, PartyShares, largestGap, namedAndOthers, sharePercent, termsText } from "./parties/TermViews.jsx";
import "./index_pages.css";
import "./parties.css";

// The share of the total as a percent with one decimal, or "under 0.1%" for a very small share.
export function shareText(n, total) {
  if (!total) return "";
  const p = (100 * n) / total;
  return p < 0.1 ? "under 0.1%" : `${p.toFixed(1)}%`;
}

// The first and the last year with a speech of any party, for example "1999 to 2026".
export function yearsText(parties) {
  const years = parties.flatMap((p) => [p.first, p.last]).filter(Boolean).map((d) => Number(d.slice(0, 4)));
  return years.length ? `${Math.min(...years)} to ${Math.max(...years)}` : "";
}

const matches = (words, name, code) => !words || `${name} ${code}`.toLowerCase().includes(words);

// The list of all parties shows this many parties as cards: the parties with the most speeches in all terms.
export const TOP_CARDS = 8;

// The page has two parts. The term block shows one Lok Sabha: the address holds the term, and with no term the newest term shows.
// The list of all parties does not change with the term.
export default function Parties() {
  const { data, loading, error, retry } = useAnswer("/api/parties");
  const [params, setParams] = useSearchParams();
  const [filter, setFilter] = useState("");
  const [asTable, setAsTable] = useState(false);

  useEffect(() => {
    document.title = "Parties · Torko";
  }, []);

  const all = data?.parties || [];
  const terms = data?.terms || [];
  const term = terms.find((t) => String(t.term) === params.get("term")) || terms[terms.length - 1];
  const colours = useMemo(() => Object.fromEntries(all.map((p) => [p.code, p.colour])), [all]);
  const words = filter.trim().toLowerCase();

  const head = (
    <div className="index-head">
      <h1 className="index-head__title">Parties in the Lok Sabha</h1>
      {data && (
        <p className="parties-lede">
          See the members of each party, how much each party speaks, and the subjects that each party speaks about.{" "}
          {formatNumber(all.length)} parties, {yearsText(all)}.
        </p>
      )}
    </div>
  );

  let body;
  if (loading && !data) body = <Loading lines={8} />;
  else if (error) body = <ErrorState error={error} onRetry={retry} />;
  else {
    const rows = term ? namedAndOthers(term.parties) : [];
    const gap = largestGap(rows);
    const showTable = asTable || Boolean(words);
    const tableRows = all.filter((p) => matches(words, p.name, p.code));
    body = (
      <div className="index-body">
        {term && (
          <section className="parties-term" aria-labelledby="parties-term-title">
            <div className="parties-term__head">
              <h2 id="parties-term-title" className="index-section-title">
                {termLong(term.term)} <span className="parties-term__years">{term.years}</span>
              </h2>
              <div className="parties-terms" role="group" aria-label="Select a Lok Sabha">
                {terms.map((t) => (
                  <Chip
                    key={t.term}
                    label={`${ordinal(t.term)} · ${t.years.slice(0, 4)}`}
                    selected={t.term === term.term}
                    onClick={() => setParams({ term: String(t.term) }, { replace: true })}
                  />
                ))}
              </div>
            </div>
            <div className="parties-term__body">
            <div className="parties-two">
            <div>
              <h3 className="index-section-title">The House, by party</h3>
              <p className="parties-note">Each dot is one member. Select a party to open its page.</p>
              <PartyHouse rows={rows} total={term.members} colours={colours} />
            </div>
            <div>
              <h3 className="index-section-title">Members and speeches</h3>
              <p className="parties-note">Upper bar: share of the members. Lower bar: share of the speeches.</p>
              <PartyShares rows={rows} colours={colours} />
              {gap && (
                <p className="parties-note">
                  {gap.code}: {sharePercent(gap.member_share)} of the members, {sharePercent(gap.speech_share)} of the speeches. This is
                  the largest difference in the {termLong(term.term)}.
                </p>
              )}
            </div>
            </div>

            {term.grid.rows.length > 0 && (
          <div className="parties-term__grid">
            <h3 id="parties-grid-title" className="index-section-title">What each party speaks about</h3>
            <p className="parties-note">
              Each cell compares a party with the full House. 2.0× means that the party gives the subject area twice the share of its
              speeches.
            </p>
            <PartyGrid grid={term.grid} />
            <div className="parties-key">
              <span><span className="parties-key__box parties-key__box--much" /> {LIFT_MUCH.toFixed(1)}× or more</span>
              <span><span className="parties-key__box parties-key__box--more" /> {LIFT_MORE.toFixed(1)}× or more</span>
              <span><span className="parties-key__box" /> near the House, or less</span>
              <span><span className="parties-key__box parties-key__box--empty" /> too few speeches</span>
            </div>
          </div>
            )}
            </div>
          </section>
        )}

        <section aria-labelledby="parties-all-title">
          <h2 id="parties-all-title" className="index-section-title">All parties</h2>
          <div className="index-tools">
            <div className="index-filter">
              <label htmlFor="parties-filter" className="index-filter__label">Find a party</label>
              <input
                id="parties-filter"
                type="search"
                className="index-filter__input"
                placeholder="Name or code, for example BJD"
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                autoComplete="off"
              />
            </div>
            {(words || showTable || all.length <= TOP_CARDS) && (
              <p className="index-count mono" role="status">
                {words
                  ? `${formatNumber(tableRows.length)} of ${formatNumber(all.length)} parties`
                  : `${formatNumber(all.length)} parties in all terms, most speeches first`}
              </p>
            )}
          </div>
          {showTable ? (
            <div className="index-table-frame">
              <table className="index-table">
                <thead>
                  <tr>
                    <th scope="col">Party</th>
                    <th scope="col" className="index-table__num">Speeches</th>
                    <th scope="col" className="index-table__num index-table__wide">Share</th>
                    <th scope="col" className="index-table__num">Members</th>
                    <th scope="col" className="index-table__wide">Terms</th>
                  </tr>
                </thead>
                <tbody>
                  {tableRows.map((p) => (
                    <tr key={p.code}>
                      <th scope="row">
                        <Link to={`/party/${encodeURIComponent(p.code)}`} className="index-table__name">{p.name}</Link>{" "}
                        <span className="index-table__code mono">{p.code}</span>
                      </th>
                      <td className="index-table__num mono">{formatNumber(p.speeches)}</td>
                      <td className="index-table__num index-table__wide mono">{shareText(p.speeches, data.total)}</td>
                      <td className="index-table__num mono">{formatNumber(p.members)}</td>
                      <td className="index-table__wide index-table__terms mono">{termsText(p.terms)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <PartyCards rows={all.slice(0, TOP_CARDS)} />
          )}
          {!words && all.length > TOP_CARDS && (
            <div className="index-section-foot parties-foot">
              <Button variant="text" onClick={() => setAsTable((v) => !v)}>
                {asTable ? `Show only the ${TOP_CARDS} parties with the most speeches` : `Show all ${formatNumber(all.length)} parties as a table`}
              </Button>
            </div>
          )}
        </section>
      </div>
    );
  }

  return (
    <PageLayout answer={head}>
      <div className="page-main">{body}</div>
    </PageLayout>
  );
}

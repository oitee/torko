import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useAnswer } from "../assets/js/useApi.js";
import { formatNumber, termShort } from "../assets/js/format.js";
import Breadcrumb from "../components/Breadcrumb.jsx";
import HowTorkoCounts from "../components/HowTorkoCounts.jsx";
import PageLayout from "../components/PageLayout.jsx";
import { ErrorState, Loading } from "../components/States.jsx";
import "./index_pages.css";

// The share of the total as a percent with one decimal, or "under 0.1%" for a very small share.
export function shareText(n, total) {
  if (!total) return "";
  const p = (100 * n) / total;
  return p < 0.1 ? "under 0.1%" : `${p.toFixed(1)}%`;
}

// The terms of a party as a short range when they follow each other: "13th–18th LS", else a list.
export function termsText(terms) {
  if (!terms?.length) return "";
  const run = terms.every((t, i) => i === 0 || t === terms[i - 1] + 1);
  if (terms.length === 1) return termShort(terms[0]);
  return run ? `${termShort(terms[0]).replace(" LS", "")}–${termShort(terms[terms.length - 1])}` : terms.map((t) => termShort(t).replace(" LS", "")).join(", ") + " LS";
}

// The Parties page lists every party with at least one speech. Each row links to the page of the party.
// The order is the order of the API: speeches, most first. A box filters the list by name or code.
export default function Parties() {
  const { data, loading, error, retry } = useAnswer("/api/parties");
  const [filter, setFilter] = useState("");

  useEffect(() => {
    document.title = "Parties · Torko";
  }, []);

  const rows = useMemo(() => {
    const words = filter.trim().toLowerCase();
    const all = data?.parties || [];
    return words ? all.filter((p) => `${p.name} ${p.code}`.toLowerCase().includes(words)) : all;
  }, [data, filter]);

  const head = (
    <div className="index-head">
      <h1 className="index-head__title">Parties</h1>
      <p className="head-description">
        {data
          ? `${formatNumber(data.count)} parties spoke in the Lok Sabha. Together they hold ${formatNumber(
              data.parties.reduce((s, p) => s + p.speeches, 0)
            )} of the ${formatNumber(data.total)} speeches with an identified member.`
          : "Every party with at least one speech in the Lok Sabha."}
      </p>
    </div>
  );

  let body;
  if (loading && !data) body = <Loading lines={8} />;
  else if (error) body = <ErrorState error={error} onRetry={retry} />;
  else
    body = (
      <>
        <div className="index-tools">
        <div className="index-filter">
          <label htmlFor="parties-filter" className="index-filter__label">
            Find a party
          </label>
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
        <p className="index-count mono" role="status">
          {rows.length === (data?.parties || []).length
            ? `${formatNumber(rows.length)} parties, most speeches first`
            : `${formatNumber(rows.length)} of ${formatNumber(data.parties.length)} parties`}
        </p>
        </div>
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
              {rows.map((p) => (
                <tr key={p.code}>
                  <th scope="row">
                    <Link to={`/party/${encodeURIComponent(p.code)}`} className="index-table__name">
                      {p.name}
                    </Link>{" "}
                    <span className="index-table__code mono">{p.code}</span>
                  </th>
                  <td className="index-table__num mono">{formatNumber(p.speeches)}</td>
                  <td className="index-table__num index-table__wide mono">{shareText(p.speeches, data.total)}</td>
                  <td className="index-table__num mono">{formatNumber(p.members)}</td>
                  <td className="index-table__wide mono">{termsText(p.terms)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </>
    );

  return (
    <PageLayout breadcrumb={<Breadcrumb items={[{ label: "Parties" }]} />} answer={head}>
      <div className="page-main">
        {body}
        <section className="index-method">
          <HowTorkoCounts>
            The party of a speech is the party of the member on the date of the debate. Speeches counts all speeches of
            the party, tagged or not. Share is the part of all speeches with an identified member. Members counts the
            members who spoke for the party.
          </HowTorkoCounts>
        </section>
      </div>
    </PageLayout>
  );
}

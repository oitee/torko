import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useAnswer } from "../assets/js/useApi.js";
import { formatNumber, termShort } from "../assets/js/format.js";
import Breadcrumb from "../components/Breadcrumb.jsx";
import Chip from "../components/Chip.jsx";
import HowTorkoCounts from "../components/HowTorkoCounts.jsx";
import PageLayout from "../components/PageLayout.jsx";
import { ErrorState, Loading } from "../components/States.jsx";
import NotFound from "./not_found.jsx";
import PartyCompare from "./party/PartyCompare.jsx";
import PartyShareChart from "./party/PartyShareChart.jsx";
import { activeTerms, headNumbers, partyColourVars } from "./party/partyData.js";
import "./party.css";

// The Party page shows the voice of one party in the Lok Sabha: its share of the tagged speeches in each term,
// the subjects and places it raises more than all parties do, and the members who lead on its top subjects.
export default function Party() {
  const { code } = useParams();
  const { data: party, loading, error, retry } = useAnswer(`/api/party/${encodeURIComponent(code)}`);
  const [term, setTerm] = useState("all");

  useEffect(() => {
    setTerm("all");
  }, [code]);


  useEffect(() => {
    if (party?.name) {
      document.title = `${party.name} · Torko`;
    } else if (error?.status === 404) {
      document.title = "Page not found · Torko";
    }
  }, [party, error]);

  if (loading) {
    return (
      <main className="party-page party-page--loading">
        <h1 className="sr-only">Party</h1>
        <Loading lines={4} />
      </main>
    );
  }

  if (error?.status === 404) return <NotFound />;

  if (error || !party) {
    return (
      <main className="party-page party-page--error">
        <ErrorState error={error} onRetry={retry} />
      </main>
    );
  }

  const pcode = party.code;
  const numbers = headNumbers(party);
  const termsWithSubjects = activeTerms(party.terms).filter((t) => t.typical.length > 0);
  const picked = term === "all" ? null : party.terms.find((t) => String(t.term) === term);
  const subjects = picked ? picked.typical : party.typical_all;
  const rules = party.rules || {};

  const head = (
    <div className="party-head">
      <div className="party-head__header">
        <h1 className="head-title">{party.name}</h1>
        <p className="party-head__code mono">{pcode}</p>
      </div>
      <dl className="head-numbers">
        {numbers.map((item) => (
          <div key={item.label} className={`party-head__stat${item.lead ? " party-head__stat--lead" : ""}`}>
            <dt className="head-stat-label">{item.label}</dt>
            <dd className="party-head__stat-value head-stat-value">{item.value}</dd>
          </div>
        ))}
      </dl>
    </div>
  );

  const termControls = (
    <ul className="chip-list" aria-label="Choose a term">
      <li>
        <Chip label="All terms" selected={term === "all"} onClick={() => setTerm("all")} />
      </li>
      {termsWithSubjects.map((t) => (
        <li key={t.term}>
          <Chip
            label={`${termShort(t.term)} · ${t.years}`}
            selected={term === String(t.term)}
            onClick={() => setTerm(String(t.term))}
          />
        </li>
      ))}
    </ul>
  );

  return (
    <div className="party-page" style={partyColourVars(pcode, party.colour)}>
      <PageLayout breadcrumb={<Breadcrumb items={[{ label: "Parties" }, { label: party.name }]} />} answer={head}>
        <div className="page-main">
          <PartyShareChart terms={party.terms} code={pcode} />

          <PartyCompare
            id="party-subjects-heading"
            title="Subjects the party raises more than the House"
            meta={picked ? `${termShort(picked.term)} · ${picked.years}` : "all terms"}
            rows={subjects}
            code={pcode}
            hrefBase="/tag/"
            controls={termControls}
            empty={`This term has fewer than ${formatNumber(rules.min_party_tagged)} tagged ${pcode} speeches. Torko shows no subjects for it.`}
          />

          <PartyCompare
            id="party-places-heading"
            title="Places the party raises more than the House"
            meta="all terms"
            rows={party.places}
            code={pcode}
            hrefBase="/place/"
            empty={`No place has ${formatNumber(rules.min_n_place)} or more tagged ${pcode} speeches from ${formatNumber(rules.min_members_place)} or more members.`}
          />

          {party.top3?.some((t) => t.members.length > 0) && (
            <section className="party-section" aria-labelledby="party-leaders-heading">
              <div className="section-header">
                <h2 id="party-leaders-heading" className="party-section__title">
                  Who speaks on these subjects
                </h2>
                <span className="party-section__meta mono">tagged speeches · all terms</span>
              </div>
              <div className="party-leaders">
                {party.top3
                  .filter((t) => t.members.length > 0)
                  .map((t) => (
                    <div key={t.slug} className="party-leaders__group">
                      <h3 className="party-leaders__title">
                        <Link to={`/tag/${t.slug}`}>{t.tag}</Link>
                      </h3>
                      <ul className="party-leaders__list">
                        {t.members.map((m) => (
                          <li key={m.id}>
                            <Link to={`/member/${m.id}`} className="party-leaders__row">
                              <span className="party-leaders__name">{m.name}</span>
                              <span className="party-leaders__count mono">{formatNumber(m.n)}</span>
                            </Link>
                          </li>
                        ))}
                      </ul>
                    </div>
                  ))}
              </div>
            </section>
          )}

          <section className="party-section party-section--method">
            <HowTorkoCounts>
              The party of a speech is the party of the member on the date of the debate. A tagged speech is a speech with
              at least one tag of any kind. For each subject, Torko compares two rates: the speeches with the subject in
              every 1,000 tagged speeches of the party, and the same rate for all parties. From the rate of all parties,
              Torko finds how many speeches the party would give on the subject. The list orders the subjects by the
              extra speeches above that number. A subject needs at least {formatNumber(rules.min_members)} members of the
              party, and {formatNumber(rules.min_n_term)} speeches of the party in one term or{" "}
              {formatNumber(rules.min_n_all)} in all terms. A place needs {formatNumber(rules.min_members_place)} members.
              Torko leaves out subjects that
              are in more than {Math.round((rules.general_share || 0) * 100)}% of all tagged speeches, procedure
              subjects, and the names of parties.
            </HowTorkoCounts>
          </section>
        </div>
      </PageLayout>
    </div>
  );
}

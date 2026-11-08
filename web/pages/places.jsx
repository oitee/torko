import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useAnswer } from "../assets/js/useApi.js";
import { formatNumber } from "../assets/js/format.js";
import HowTorkoCounts from "../components/HowTorkoCounts.jsx";
import PageLayout from "../components/PageLayout.jsx";
import { ErrorState, Loading } from "../components/States.jsx";
import "./index_pages.css";

// Keep the states and seats whose name holds the words. A state that matches keeps all its seats.
export function filterStates(states, words) {
  const w = (words || "").trim().toLowerCase();
  if (!w) return states;
  return states
    .map((s) => (s.name.toLowerCase().includes(w) ? s : { ...s, seats: s.seats.filter((x) => x.name.toLowerCase().includes(w)) }))
    .filter((s) => s.seats.length || s.name.toLowerCase().includes(w));
}

function PlaceName({ place }) {
  const name = place.page ? <Link to={`/place/${place.slug}`}>{place.name}</Link> : <span>{place.name}</span>;
  return (
    <>
      {name}
      {place.speeches != null && <span className="index-places__n mono"> {formatNumber(place.speeches)}</span>}
    </>
  );
}

export default function Places() {
  const { data, loading, error, retry } = useAnswer("/api/places");
  const [filter, setFilter] = useState("");

  useEffect(() => {
    document.title = "Places · Torko";
  }, []);

  const states = useMemo(() => filterStates(data?.states || [], filter), [data, filter]);
  const shownSeats = states.reduce((n, s) => n + s.seats.length, 0);

  const head = (
    <div className="index-head">
      <h1 className="index-head__title">Places</h1>
      <p className="head-description">
        {data
          ? `${formatNumber(data.seat_count)} Lok Sabha seats in ${formatNumber(data.state_count)} states and union territories. Each number counts the speeches that carry the tag of the place.`
          : "The Lok Sabha seats of each state and union territory."}
      </p>
    </div>
  );

  let body;
  if (loading && !data) body = <Loading lines={8} />;
  else if (error) body = <ErrorState error={error} onRetry={retry} />;
  else
    body = (
      <>
        {data.featured?.length > 0 && (
          <section className="index-featured" aria-labelledby="places-featured">
            <h2 id="places-featured" className="index-section-title">
              Seats in the most speeches
            </h2>
            <ol className="index-featured__list">
              {data.featured.map((f) => (
                <li key={f.slug}>
                  <Link to={`/place/${f.slug}`}>{f.name}</Link>
                  <span className="index-featured__state">{f.state}</span>
                  <span className="mono">{formatNumber(f.speeches)} speeches</span>
                </li>
              ))}
            </ol>
          </section>
        )}
        <div className="index-tools">
        <div className="index-filter">
          <label htmlFor="places-filter" className="index-filter__label">
            Find a state or a seat
          </label>
          <input
            id="places-filter"
            type="search"
            className="index-filter__input"
            placeholder="For example Latur, or Kerala"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            autoComplete="off"
          />
        </div>
        <p className="index-count mono" role="status">
          {filter.trim()
            ? `${formatNumber(shownSeats)} seats in ${formatNumber(states.length)} states match`
            : "States and seats from A to Z"}
        </p>
        </div>
        <div className="index-places">
          {states.map((s) => (
            <section key={s.slug} className="index-places__state" aria-label={s.name}>
              <h2 className="index-places__title">
                <PlaceName place={s} />
              </h2>
              {s.seats.length > 0 && (
                <ul className="index-places__seats">
                  {s.seats.map((x) => (
                    <li key={x.slug}>
                      <PlaceName place={x} />
                    </li>
                  ))}
                </ul>
              )}
            </section>
          ))}
        </div>
      </>
    );

  return (
    <PageLayout answer={head}>
      <div className="page-main">
        {body}
        <section className="index-method">
          <HowTorkoCounts>
            A number counts the speeches that carry the tag of the place, each speech once. A speech that only names the
            place in its words, with no tag, is not in the count. A name with no link has no page yet.
          </HowTorkoCounts>
        </section>
      </div>
    </PageLayout>
  );
}

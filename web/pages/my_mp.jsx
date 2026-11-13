import React, { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useAnswer } from "../assets/js/useApi.js";
import { formatNumber } from "../assets/js/format.js";
import Button from "../components/Button.jsx";
import HowTorkoCounts from "../components/HowTorkoCounts.jsx";
import PageLayout from "../components/PageLayout.jsx";
import { EmptyState, ErrorState, Loading } from "../components/States.jsx";
import SeatCard from "./my_mp/SeatCard.jsx";
import "./my_mp.css";

const MAX_SUGGESTIONS = 8;

// Split the words in the box into the seat words and the state words. "Latur, Maharashtra" gives both parts.
export function splitQuery(text) {
  const [seat, ...rest] = String(text || "").split(",");
  return { seat: seat.trim(), state: rest.join(",").trim() };
}

// The seats of the list that fit the words in the box, best first: names that start with the words, then names that hold them.
// states: the list of /api/places. A state part after a comma keeps only the seats of the states that start with it.
export function suggestSeats(states, text, limit = MAX_SUGGESTIONS) {
  const { seat, state } = splitQuery(text);
  const k = seat.toLowerCase();
  if (!k) return [];
  const st = state.toLowerCase();
  const starts = [];
  const inside = [];
  for (const s of Array.isArray(states) ? states : []) {
    if (st && !s.name.toLowerCase().startsWith(st)) continue;
    for (const x of s.seats || []) {
      const n = x.name.toLowerCase();
      if (n.startsWith(k)) starts.push({ ...x, state: s.name });
      else if (n.includes(k)) inside.push({ ...x, state: s.name });
    }
  }
  return [...starts, ...inside].slice(0, limit);
}

// The Your MP page finds the seats whose name matches the words in the box.
// For each seat, it shows the member now, the subjects of most of their speeches, and the members before.
// The words live in the address (?q=), so a reader can share the result.
export default function MyMp() {
  const [searchParams, setSearchParams] = useSearchParams();
  const q = (searchParams.get("q") || "").trim();
  const { seat: seatWords, state: stateWords } = splitQuery(q);
  const [input, setInput] = useState(q);
  const [focused, setFocused] = useState(false);
  const { data: result, loading, error, retry } = useAnswer(seatWords ? "/api/my-mp" : null, seatWords ? { q: seatWords } : undefined);
  // The list of all seats gives the suggestions and the example seats. If it fails, the box still works.
  const { data: places } = useAnswer("/api/places");
  const suggestions = useMemo(
    () => (focused && input.trim() !== q ? suggestSeats(places?.states, input) : []),
    [places, input, focused, q]
  );

  useEffect(() => {
    setInput(q);
  }, [q]);

  useEffect(() => {
    document.title = q ? `Your MP · ${q} · Torko` : "Your MP · Torko";
  }, [q]);

  const submit = (event) => {
    if (event) event.preventDefault();
    const next = input.trim();
    setSearchParams(next ? { q: next } : {});
  };

  const pick = (seat) => {
    setInput(seat.name);
    setSearchParams({ q: seat.name });
    setFocused(false);
  };

  const head = (
    <div className="my-mp-head">
      <h1 className="head-title">Find your MP</h1>
      <p className="head-description">
        Type the name of your Lok Sabha seat. You can add the state after a comma, for example Latur, Maharashtra. Torko
        shows the member for the seat now, how often they spoke, the subjects of most of their speeches, and the members
        before them.
      </p>
      <form role="search" className="my-mp-form" onSubmit={submit} noValidate>
        <label htmlFor="my-mp-seat" className="my-mp-form__label">
          Lok Sabha seat
        </label>
        <div className="my-mp-form__bar">
          <input
            id="my-mp-seat"
            type="search"
            className="my-mp-form__input"
            placeholder="For example Latur"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            autoComplete="off"
            onFocus={() => setFocused(true)}
            onBlur={() => setTimeout(() => setFocused(false), 150)}
          />
          <div className="my-mp-form__button">
            <Button variant="primary" onClick={submit}>
              Find your MP
            </Button>
          </div>
        </div>
        {suggestions.length > 0 && (
          <ul className="my-mp-suggest" aria-label="Seats that fit the words">
            {suggestions.map((x) => (
              <li key={`${x.state}-${x.slug}`}>
                <button type="button" className="my-mp-suggest__item" onMouseDown={(e) => e.preventDefault()} onClick={() => pick(x)}>
                  <span>{x.name}</span>
                  <span className="my-mp-suggest__state mono">{x.state}</span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </form>
    </div>
  );

  const allSeats = result?.seats || [];
  const seatState = (x) => x.current?.[0]?.state || x.older?.[0]?.state || "";
  const seats = stateWords
    ? allSeats.filter((x) => seatState(x).toLowerCase().startsWith(stateWords.toLowerCase()))
    : allSeats;
  const featured = Array.isArray(places?.featured) ? places.featured : [];

  let body = null;
  if (!q) {
    body = (
      <section className="my-mp-start" aria-labelledby="my-mp-start-heading">
        <h2 id="my-mp-start-heading" className="my-mp-start__title">
          How to find your seat
        </h2>
        <ol className="my-mp-start__steps">
          <li>Type the name of your town or of your Lok Sabha seat in the box.</li>
          <li>Pick a seat from the list, or press the button.</li>
          <li>Read who speaks for the seat now, and what they speak about.</li>
        </ol>
        <p className="my-mp-start__note">A seat can have a different name from the town.</p>
        {featured.length > 0 && (
          <>
            <h3 className="my-mp-start__sub">Example seats</h3>
            <p className="my-mp-start__note">
              The {featured.length} seats with the most speeches that carry the place tag, most first.
            </p>
            <ol className="my-mp-start__examples">
              {featured.map((f) => (
                <li key={f.slug}>
                  <Link to={`/my-mp?q=${encodeURIComponent(f.name)}`} className="my-mp-start__example">
                    <span className="my-mp-start__example-name">{f.name}</span>
                    <span className="my-mp-start__example-state">{f.state}</span>
                  </Link>
                </li>
              ))}
            </ol>
          </>
        )}
      </section>
    );
  } else if (loading) {
    body = <Loading lines={4} />;
  } else if (error) {
    body = <ErrorState error={error} onRetry={retry} />;
  } else if (seats.length === 0) {
    body = (
      <EmptyState>
        No Lok Sabha seat has “{seatWords}” in its name{stateWords ? ` in a state that starts with “${stateWords}”` : ""}. Check
        the spelling, or type a part of the name. You can also{" "}
        <Link to={`/search?q=${encodeURIComponent(seatWords)}`}>search the speeches</Link>.
      </EmptyState>
    );
  } else {
    const first = seats[0];
    body = (
      <div className="my-mp-results">
        <p className="my-mp-count" role="status">
          {seats.length === 1
            ? `Found 1 seat: ${first.seat}${seatState(first) ? `, ${seatState(first)}` : ""}.`
            : `Found ${formatNumber(seats.length)} seats with “${seatWords}” in the name.`}
          {allSeats.length >= 12 ? " Torko shows at most 12 seats. Add more of the name to narrow the list." : ""}
        </p>
        <div className="my-mp-results__seats">
          {seats.map((s) => (
            <SeatCard key={s.seat} seat={s} latestTerm={result.latest_term} />
          ))}
        </div>
      </div>
    );
  }

  return (
    <PageLayout answer={head}>
      <div className="page-main">
        {body}
        {q && (
          <section className="my-mp-method">
            <HowTorkoCounts />
          </section>
        )}
      </div>
    </PageLayout>
  );
}

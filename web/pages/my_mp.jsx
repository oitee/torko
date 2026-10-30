import React, { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { getJSON } from "../assets/js/api.js";
import { formatNumber } from "../assets/js/format.js";
import Breadcrumb from "../components/Breadcrumb.jsx";
import Button from "../components/Button.jsx";
import HowTorkoCounts from "../components/HowTorkoCounts.jsx";
import PageLayout from "../components/PageLayout.jsx";
import { EmptyState, ErrorState, Loading } from "../components/States.jsx";
import SeatCard from "./my_mp/SeatCard.jsx";
import "./my_mp.css";

// The Your MP page finds the seats whose name matches the words in the box.
// For each seat, it shows the member now, the subjects of most of their speeches, and the members before.
// The words live in the address (?q=), so a reader can share the result.
export default function MyMp() {
  const [searchParams, setSearchParams] = useSearchParams();
  const q = (searchParams.get("q") || "").trim();
  const [input, setInput] = useState(q);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchSeats = () => {
    if (!q) {
      setResult(null);
      setError(null);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    getJSON("/api/my-mp", { q })
      .then((data) => {
        setResult(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err);
        setLoading(false);
      });
  };

  useEffect(() => {
    setInput(q);
    fetchSeats();
  }, [q]);

  useEffect(() => {
    document.title = q ? `Your MP · ${q} · Torko` : "Your MP · Torko";
  }, [q]);

  const submit = (event) => {
    if (event) event.preventDefault();
    const next = input.trim();
    setSearchParams(next ? { q: next } : {});
  };

  const head = (
    <div className="my-mp-head">
      <h1 className="my-mp-head__title">Find your MP</h1>
      <p className="my-mp-head__description">
        Type the name of your Lok Sabha seat. Torko shows the member for the seat now, the subjects of most of their
        speeches, and the members before them.
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
          />
          <div className="my-mp-form__button">
            <Button variant="primary" onClick={submit}>
              Find your MP
            </Button>
          </div>
        </div>
      </form>
    </div>
  );

  const seats = result?.seats || [];

  let body = null;
  if (!q) {
    body = null;
  } else if (loading) {
    body = <Loading lines={4} />;
  } else if (error) {
    body = <ErrorState error={error} onRetry={fetchSeats} />;
  } else if (seats.length === 0) {
    body = <EmptyState>No Lok Sabha seat has “{q}” in its name. Check the spelling, or type a part of the name.</EmptyState>;
  } else {
    body = (
      <div className="my-mp-results">
        <p className="my-mp-count mono" role="status">
          {seats.length === 1
            ? `1 seat has “${q}” in its name`
            : `${formatNumber(seats.length)} seats have “${q}” in their name`}
          {seats.length >= 12 ? ". Torko shows at most 12 seats. Type more of the name to find others." : ""}
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
    <PageLayout breadcrumb={<Breadcrumb items={[{ label: "Your MP" }]} />} answer={head}>
      <div className="my-mp-main">
        {body}
        <section className="my-mp-method">
          <HowTorkoCounts>
            Torko matches the words to any part of a seat name. A seat name does not include its state. The subjects are
            the 5 tags that most speeches of the member carry, in all terms. The number on each tag counts those
            speeches. Torko leaves out tags for roles, people and places.
          </HowTorkoCounts>
        </section>
      </div>
    </PageLayout>
  );
}

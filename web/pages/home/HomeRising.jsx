import React from "react";
import { Link } from "react-router-dom";
import { formatDateLong, formatNumber, ordinal } from "../../assets/js/format.js";
import "./HomeRising.css";

// The most subjects that the block shows.
export const MAX_RISING = 5;

// The page of a subject. A place has its own page, and every other tag opens the tag page.
function subjectHref(subject) {
  return subject.type === "place" ? `/place/${subject.slug}` : `/tag/${subject.slug}`;
}

// HomeRising lists the subjects that rose in the newest session. It shows that the data is current.
// The list is the first MAX_RISING subjects of /api/home → typical, in the order of the answer.
// The API orders them by lift: the share of the session speeches that carry the subject,
// divided by the share of all speeches of the term that carry it.
export default function HomeRising({ typical, session, term, first, last }) {
  const list = (Array.isArray(typical) ? typical : []).slice(0, MAX_RISING);
  if (list.length === 0) return null;

  return (
    <section className="home-rising" aria-labelledby="home-rising-title">
      <h2 id="home-rising-title" className="home-rising__title">
        Subjects that rose in the newest session
      </h2>
      <ul className="home-rising__list">
        {list.map((subject) => (
          <li key={subject.slug} className="home-rising__item">
            <Link to={subjectHref(subject)} className="home-rising__name">
              {subject.name}
            </Link>
            <span className="home-rising__count">
              {formatNumber(subject.speeches_in_session ?? subject.n)} speeches
            </span>
          </li>
        ))}
      </ul>
      <p className="home-rising__meta">
        {session != null && term != null && (
          <>
            Newest session: session {session} of the {ordinal(term)} Lok Sabha
            {first && last ? `, ${formatDateLong(first)} to ${formatDateLong(last)}` : ""}.{" "}
          </>
        )}
        Torko ranks a subject by its share of the speeches of this session, against its share of all speeches
        of the term. The list shows the {list.length} highest.
      </p>
    </section>
  );
}

export { HomeRising };

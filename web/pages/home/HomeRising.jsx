import React from "react";
import { Link } from "react-router-dom";
import { formatNumber, ordinal } from "../../assets/js/format.js";
import "./HomeRising.css";

export const MAX_RISING = 6;

// The page of a topic. A place has its own page, and every other tag opens the tag page.
function subjectHref(subject) {
  return subject.type === "place" ? `/place/${subject.slug}` : `/tag/${subject.slug}`;
}

export function sessionLine(sessionLabel, term) {
  const parts = [sessionLabel ? `${sessionLabel} session` : "", term != null ? `${ordinal(term)} Lok Sabha` : ""].filter(Boolean);
  return parts.length ? `(${parts.join(", ")})` : "";
}

// The first MAX_RISING topics of /api/home → typical, in the order of the answer (by lift).
// The number in brackets counts the speeches of the session that carry the topic.
export default function HomeRising({ typical, sessionLabel, term }) {
  const list = (Array.isArray(typical) ? typical : []).slice(0, MAX_RISING);
  if (list.length === 0) return null;
  const line = sessionLine(sessionLabel, term);

  return (
    <section className="home-rising" aria-labelledby="home-rising-title">
      <div className="home-rising__head">
        <h2 id="home-rising-title" className="home-rising__title">Topics trending this session</h2>
        {line && <p className="home-rising__session">{line}</p>}
      </div>
      <ul className="home-rising__list">
        {list.map((subject) => {
          const n = subject.speeches_in_session ?? subject.n;
          return (
            <li key={subject.slug}>
              <Link to={subjectHref(subject)} className="home-rising__chip" aria-label={`${subject.name}, trending, ${formatNumber(n)} speeches this session`}>
                <span className="home-rising__name">{subject.name}</span>
                <svg className="home-rising__up" viewBox="0 0 10 10" width="10" height="10" aria-hidden="true">
                  <path d="M5 1 L9.5 8.5 L0.5 8.5 Z" fill="currentColor" />
                </svg>
                <span className="home-rising__count">({formatNumber(n)})</span>
              </Link>
            </li>
          );
        })}
      </ul>
    </section>
  );
}

export { HomeRising };
